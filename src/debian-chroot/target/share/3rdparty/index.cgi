#!/usr/local/perl/bin/perl -w
# Copyright 2010 Antoine Bertin
# <diaoulael [ignore this] at users.sourceforge period net>
#
# This file is part of syno-packager.
#
# syno-packager is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# syno-packager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with syno-packager.  If not, see <http://www.gnu.org/licenses/>.

use strict;
use warnings;
use CGI;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use DBI;
use Switch;

# Const
my $SYAUTH = '/usr/syno/synoman/webman/modules/authenticate.cgi|';
my $DBPATH = '/usr/local/debian-chroot/manager/manager.db';
my $CRCMD = '/usr/local/debian-chroot/bin/chroot';
my $CRTGT = '/usr/local/debian-chroot/chroottarget';

# CGI
my $q = CGI->new;

# Check auth
if (!&isAuthed()) {
	print $q->header;
	print $q->start_html('Debian Chroot Manager - Authentication required');
	print $q->h4('Please connect to DSM to continue...');
	print $q->end_html;
	exit 0;
}

# Controller
my $dbh = DBI->connect('DBI:SQLite:dbname='.$DBPATH,'','');
die 'Connect failed: '.DBI->errstr() unless $dbh; 

switch(lc($q->param('action'))) {
	case 'add'		{ &addProcess($q->param('name'), $q->param('launch_script'), $q->param('status_command')); }
	case 'del'		{ &delProcess($q->param('id')); }
	case 'start'	{ &startProcess($q->param('id')); }
	case 'stop'		{ &stopProcess($q->param('id')); }
	else 			{ &showPage(); }
}
$dbh->disconnect;
if ($q->param('action') ne '') {
	print $q->redirect('index.cgi');
}

#############
# Functions #
#############
#
# Add a process
sub addProcess {
	my ($name, $launch_script, $status_command) = @_;
	my $sth = $dbh->prepare('INSERT INTO processes (name, launch_script, status_command) VALUES (?, ?, ?)');
	$sth->execute($name, $launch_script, $status_command);
}

# Delete a process
sub delProcess {
	my ($id) = @_;
	my $sth = $dbh->prepare('DELETE FROM processes WHERE id = ?');
	$sth->execute($id);
}

# Start a process
sub startProcess {
	my ($id) = @_;
	my $sth = $dbh->prepare('SELECT launch_script FROM processes WHERE id = ?');
	$sth->execute($id);
	my $launch_script = $sth->fetchrow_array;
	my $launch_result = system($CRCMD.' '.$CRTGT.' '.$launch_script.' start > /dev/null 2>&1');
	#TODO: Do something with that result
}

# Stop a process
sub stopProcess {
	my ($id) = @_;
	my $sth = $dbh->prepare('SELECT launch_script FROM processes WHERE id = ?');
	$sth->execute($id);
	my $launch_script = $sth->fetchrow_array;
	my $launch_result = system($CRCMD.' '.$CRTGT.' '.$launch_script.' stop > /dev/null 2>&1');
	#TODO: Do something with that result
}

# List processes
sub showPage {
	# Show the table header (and init)
	print $q->header,
		$q->start_html(-title=>'Debian Chroot Manager',
			-author=>'diaoulael@gmail.com',
			-style=>{-src=>'css/main.css'},
			-script=>[{-type=>'text/javascript', -src=>'js/lib/jquery-1.6.1.min.js'},
				{-type=>'text/javascript', -src=>'js/lib/jquery.dataTables.min.js'},
				{-type=>'text/javascript', -src=>'js/main.js'}
			]
		),
		$q->start_form(-action=>'index.cgi'),
		$q->start_table({-id=>'processes', -border=>0, -cellspacing=>0, -cellpadding=>0}),
		$q->start_thead,
		$q->start_Tr,
		$q->th('Name'),
		$q->th('Launch script'),
		$q->th('Status Command'),
		$q->th('Status'),
		$q->th('Actions'),
		$q->end_Tr,
		$q->end_thead;

	# Show all processes in the table body
	print $q->start_tbody;
	my $sth = $dbh->prepare('SELECT id, name, launch_script, status_command FROM processes');
	$sth->execute();
	while (my ($id, $name, $launch_script, $status_command) = $sth->fetchrow_array()) {
		# Get the status if we have a status command
		my $status = 'N/A';
		my $launch_action = '';
		if ($status_command ne '') {
			$status = 'Stopped';
			$launch_action = 'start';
			my $status_result = system($CRCMD.' '.$CRTGT.' /bin/bash -c \''.$status_command.'\' > /dev/null 2>&1');
			if ($status_result eq 0) {
				$status = 'Running';
				$launch_action = 'stop';
			}
		}
		print $q->start_Tr,
			$q->td($name),
			$q->td($launch_script),
			$q->td($status_command),
			$q->td($status),
			$q->td($q->a({-href=>'index.cgi?action=del&id='.$id}, 'Del').' '.$q->a({-href=>'index.cgi?action='.$launch_action.'&id='.$id}, ucfirst($launch_action))),
			$q->end_Tr;
	}
	print $q->end_tbody;

	# Show the form in the table footer (and close)
	print $q->start_tfoot,
		$q->start_Tr,
		$q->td($q->textfield(-name=>'name', -value=>'', -maxlength=>25, -size=>25)),
		$q->td($q->textfield(-name=>'launch_script', -value=>'', -size=>40)),
		$q->td({-colspan=>2}, $q->textfield(-name=>'status_command', -value=>'', -size=>60)),
		$q->td($q->submit(-name => 'action', -id => 'add_submit', -value => 'Add'),),
		$q->end_Tr,
		$q->end_tfoot,
		$q->end_table,
		$q->end_form,
		$q->end_html;
}


#############
# Functions #
#############
#
# Check for user's authentication
sub isAuthed {
	my $user;
	if (open(IN,$SYAUTH)) {
		$user=<IN>;
		if (defined($user)) {
			chop($user);
		}
		close(IN);
	}
	if (!$user || $user ne 'admin') {
		return 0;
	}
	return 1;
}
