#!/usr/bin/perl -w
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

# Import Config::Crontab module
use lib "/usr/local/toolbox/lib/perl5";
use Config::Crontab;

# Const
my $SYAUTH = '/usr/syno/synoman/webman/modules/authenticate.cgi|';

# CGI
my $q = CGI->new;

# Check auth
if (!&isAuthed()) {
	print $q->header;
	print $q->start_html('Cron Manager - Authentication required');
	print $q->h4('Please connect to DSM to continue...');
	print $q->end_html;
	exit 0;
}

# Controller
my $ct = new Config::Crontab(-file=>'/etc/crontab', -system=>1);
switch(lc($q->param('action'))) {
	case 'add'		{ &addTask($q->param('minute'), $q->param('hour'), $q->param('dom'), $q->param('month'), $q->param('dow'), $q->param('user'), $q->param('command')); }
	case 'del'		{ &delTask($q->param('id')); }
	case 'enable'	{ &enableTask($q->param('id')); }
	case 'disable'	{ &disableTask($q->param('id')); }
	else 			{ &showPage(); }
}
if ($q->param('action') ne '') {
	print $q->redirect('index.cgi');
}

#############
# Functions #
#############
#
# Add a task
sub addTask {
	my ($minute, $hour, $dom, $month, $dow, $user, $command) = @_;
	my $block = new Config::Crontab::Block;
	$block->last( new Config::Crontab::Event(-minute => $minute, -hour => $hour, -dom => $dom, -month => $month, -dow => $dow, -user => $user, -command => $command) );
	$ct->last($block);
	$ct->write;
}

# Delete a task
sub delTask {
	my ($id) = @_;
	my @events = $ct->select(-type => 'event');
	my $block = $ct->block(@events[$id]);
	$ct->remove($block);
	$ct->write;
}

# Enable a task
sub enableTask {
	my ($id) = @_;
	my @events = $ct->select(-type => 'event');
	@events[$id]->active(1);
	$ct->write;
}

# Disable a task
sub disableTask {
	my ($id) = @_;
	my @events = $ct->select(-type => 'event');
	@events[$id]->active(0);
	$ct->write;
}

# List tasks
sub showPage {
	# Show the table header (and init)
	print $q->header,
		$q->start_html(-title=>'Cron Manager',
			-author=>'diaoulael@gmail.com',
			-style=>{-src=>'css/main.css'},
			-script=>[{-type=>'text/javascript', -src=>'js/lib/jquery-1.6.1.min.js'},
				{-type=>'text/javascript', -src=>'js/lib/jquery.dataTables.min.js'},
				{-type=>'text/javascript', -src=>'js/main.js'}
			]
		),
		$q->start_form(-action=>'index.cgi'),
		$q->start_table({-id=>'tasks', -border=>0, -cellspacing=>0, -cellpadding=>0}),
		$q->start_thead,
		$q->start_Tr,
		$q->th('Minute'),
		$q->th('Hour'),
		$q->th('Day of month'),
		$q->th('Month'),
		$q->th('Day of week'),
		$q->th('User'),
		$q->th('Command'),
		$q->th('Status'),
		$q->th('Actions'),
		$q->end_Tr,
		$q->end_thead;

	# Show all tasks in the table body
	my $id = 0;
	for my $event ($ct->select(-type => 'event')) {
		my $active_action = 'enable';
		my $active_status = 'Disabled';
		if ($event->active) {
			$active_action = 'disable';
			$active_status = 'Enabled';
		}
		print $q->start_Tr,
			$q->td($event->minute),
			$q->td($event->hour),
			$q->td($event->dom),
			$q->td($event->month),
			$q->td($event->dow),
			$q->td($event->user),
			$q->td($event->command),
			$q->td($active_status),
			$q->td($q->a({-href=>'index.cgi?action=del&id='.$id}, 'Del').' '.$q->a({-href=>'index.cgi?action='.$active_action.'&id='.$id}, ucfirst($active_action))),
			$q->end_Tr;
		$id++;
	}
	print $q->end_tbody;

	# Show the form in the table footer (and close)
	print $q->start_tfoot,
		$q->start_Tr,
		$q->td($q->textfield(-name=>'minute', -value=>'', -maxlength=>2, -size=>5)),
		$q->td($q->textfield(-name=>'hour', -value=>'', -maxlength=>2, -size=>5)),
		$q->td($q->textfield(-name=>'dom', -value=>'', -maxlength=>2, -size=>5)),
		$q->td($q->textfield(-name=>'month', -value=>'', -maxlength=>2, -size=>5)),
		$q->td($q->textfield(-name=>'dow', -value=>'', -maxlength=>2, -size=>5)),
		$q->td($q->textfield(-name=>'user', -value=>'', -maxlength=>30, -size=>30)),
		$q->td({-colspan=>2}, $q->textfield(-name=>'command', -value=>'', -size=>60)),
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
