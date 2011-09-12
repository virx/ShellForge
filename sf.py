#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""
Copyright (C) 2011  Virgo Pihlapuu

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
# import gtk
try:
	import gtk
except:
	print >> sys.stderr, "You need to install the python gtk bindings"
	sys.exit(1)
 
# import vte
try:
	import vte
except:
	error = gtk.MessageDialog (None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
	'You need to install python bindings for libvte')
	error.run()
	sys.exit (1)

# import other things
import sys

# globals
window = None
notebook = None
tabs = None
coms = None

print """ShellForge Copyright (C) 2011  Virgo Pihlapuu
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it.
"""

# read config.txt file
def read_conf():
	fs = ''
	with open('config.txt', 'r') as f:
		fs = f.read()
	return fs
	
# clean string from lines with hashes
def clean_hash_lines(bad_s):
	clean_s = ''
	txt_arr = bad_s.splitlines()
	for line in txt_arr:
		if len(line) > 0:
			if line.strip()[0] != '#':
				clean_s += (line + "\n")
	return clean_s
	
def clean_tooltip_msg(s):
	if len(s) > 100:
		return s[0:100] + " ..."
	else:
		return s

# parse tabs and buttons from config.txt file into array
def parse_conf():
	fs_arr = clean_hash_lines(read_conf()).split('|')
	fs_i = 0
	tabs_new = []
	coms_new = []
	for part in fs_arr:
		if part.strip() == 'tab':
			tabs_new.append([fs_arr[fs_i+1], fs_arr[fs_i+2].splitlines()])
		elif part == 'command':
			coms_new.append([fs_arr[fs_i+1], fs_arr[fs_i+2]])
		fs_i += 1
	#print "============== Commands ==========="
	#print coms_new
	#print "=============== Tabs =============="
	#print tabs_new
	return tabs_new, coms_new
	
def new_terminal(win,term,pane):
	term.destroy()
	vt = vte.Terminal()
	vt.connect('child-exited', lambda term: new_terminal(pane))
	vt.fork_command()
	pane.add1(vt)
	window.show_all()
	
def get_tab(t_name):
	global tabs
	t = []
	for tab in tabs:
		if tab[0] == t_name: t = tab
	return t

def click_release_notebook(widget, event):
	if event.type == gtk.gdk.BUTTON_RELEASE:
		# get terminal widget inside this tab
		term_widget = notebook.get_nth_page(notebook.get_current_page()).get_children()[0].get_children()[0]
		#print "left click release focus widget: %r" % term_widget.__class__
		term_widget.grab_focus()

def click_release_terminal(widget, event):
	global notebook
	if event.type == gtk.gdk.BUTTON_RELEASE and event.button == 3:
		# make widget popup
		widget.popup(None, None, None, event.button, event.time)

class VteNotebook(gtk.Notebook):
	def __init__(self):
		gtk.Notebook.__init__(self)
		# set the tab properties
		self.set_property('homogeneous', True)
		# do not show the tab if there is only one tab
		self.set_property('show-tabs', False)
		# tabs on top
		self.set_tab_pos(gtk.POS_TOP)
		
		# right click menu inside vte
		self.menu = gtk.Menu()
		self.menu_item = gtk.MenuItem("Copy")
		self.menu_item_2 = gtk.MenuItem("Paste")
		
		self.menu.append(self.menu_item)
		self.menu.append(self.menu_item_2)
		
		self.menu_item.connect("activate", self.cp)
		self.menu_item_2.connect("activate", self.pst)
		
		self.menu.show()
		self.menu_item.show()		
		self.menu_item_2.show()
		
	# copy selection from current terminal
	def cp(self, widget):
		cur_page_vt = self.get_nth_page(self.get_current_page()).get_children()[0].get_children()[0]
		print cur_page_vt.__class__
		cp_txt = cur_page_vt.copy_clipboard ()
	
	# paste to current terminal
	def pst(self, widget):
		cur_page_vt = self.get_nth_page(self.get_current_page()).get_children()[0].get_children()[0]
		cur_page_vt.paste_clipboard ()

	def new_tab(self,t_name="tab_name"):
		# we create virtual terminal and put it into tab
		nbpages = self.get_n_pages()

		# virtual terminal for each tab
		vt = vte.Terminal()
		vt.fork_command()
		vt_scroll = gtk.ScrolledWindow()
		vt_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		vt_scroll.add(vt)
		vt.grab_focus()
		vt_scroll.set_size_request(500, 200)
		vt.connect_object("button_release_event", click_release_terminal, self.menu)
		
		# box for command buttons
		vbx = gtk.VBox(False,0)
		
		# scrollbar for command button box
		vb_scroll = gtk.ScrolledWindow()
		vb_scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
		vb_scroll.add_with_viewport(vbx)
		
		# vertical panes inside ta separating terminal and buttons
		h_box = gtk.HBox()
		h_box.pack_start(vt_scroll,expand=True,fill=True)
		h_box.pack_start(vb_scroll,expand=False,fill=True)
		
		lbl = gtk.Label(t_name)
		self.append_page(h_box,lbl)
		vt.connect('child-exited', self.close_tab, h_box)
		
		# tooltip for command button content
		tooltips = gtk.Tooltips()

		# create command buttons for this tab
		tab = get_tab(t_name)
		if tab[0] != '':
			ci = 1
			for cm in coms:
				for n in range(0,(len(tab[1]))):
					if cm[0].strip() == tab[1][n].strip('\n'):
						b = gtk.Button(cm[0])
						b.unset_flags(gtk.CAN_FOCUS)
						vbx.pack_start(b, expand=False, fill=False)
						b.connect('clicked', self.execute_button, vt, cm[1])
						tooltips.set_tip(b, clean_tooltip_msg(cm[1]))
				ci += 1

		# show tabs if there is more than 1
		if nbpages + 1 > 1:
			self.set_property('show-tabs', True)

		self.show_all()
		self.set_current_page(nbpages)
	
	# command button click event to execute command sequence in its tab terminal
	def execute_button(self, event, vt_widget, exec_commands):
		vt_widget.grab_focus()
		vt_widget.feed_child(exec_commands)
	
	# close current tab
	def close_tab(self, widget, child):
		pagenum = self.page_num(child)

		if pagenum != -1:
			self.remove_page(pagenum)
			child.destroy()
		if self.get_n_pages() == 1:
			self.set_property('show-tabs', False)

# main class, PyGtkVte object
class PyGtkVte:
	def __init__(self, sf_title='ShellForge'):
		global tabs, coms, notebook
		tabs, coms = parse_conf()
		
		window = gtk.Window()
		window.set_title(sf_title)
		window.connect('delete-event', lambda window, event: gtk.main_quit())

		notebook = VteNotebook()
		window.add(notebook)
		
		tn = 0
		for tab in tabs:
			notebook.new_tab(tab[0])
			tn += 1

		window.show_all()
		notebook.unset_flags(gtk.CAN_FOCUS)
		notebook.get_nth_page(notebook.get_current_page()).get_children()[0].get_children()[0].grab_focus()
		notebook.connect("button_release_event",click_release_notebook)
		
# start gtk
def main():
	gtk.main()
	return 0

# check args and call main class
if __name__ == '__main__':
	if len(sys.argv) > 1:
		sys.stderr.write("Too many arguments! Try like this: sf.py 'title'.\n")
		sys.exit(1)
	PyGtkVte('sf')
	main()
