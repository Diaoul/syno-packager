#!/usr/bin/perl
print "Content-type: text/html\n\n";

read(STDIN, $FormData, $ENV{'CONTENT_LENGTH'});
@pairs = split(/&/, $FormData);
foreach $pair (@pairs) {
	($name, $value) = split(/=/, $pair);
	$value =~ tr/+/ /;
	$value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
	$value =~ s/\r\n/\n/g; # windows fix
	$value =~ s/\r/\n/g; # mac fix
	$FORM{$name} = $value;
}

# Are we authenticated yet ?

if (open (IN,"/usr/syno/synoman/webman/modules/authenticate.cgi|")) {
	$user=<IN>;
	chop($user);
	close(IN);
}


# if not admin or no user at all...no authentication...so, bye-bye

if ($user ne 'admin') {
	print "<HTML><HEAD><TITLE>Login Required</TITLE></HEAD><BODY>Please login as admin first, before using this webpage</BODY></HTML>\n";
	die;
}

$dir=$0;
$dir=~s#/[^/]+$##g;

$do{'Config File Editor'}=$dir .'/' .'configfiles.txt';
$do{'Config File Editor.original'}=$dir .'/' .'Config File Editor.original';

if (open(IN,'configfiles.txt')) { 
	while(<IN>) {
		chop();
		if ((!(/^#/))&&(/,/)) { 
			($script,$name)=/([^,]+),([^,]+)/;
			$name=~s/^\s*//g;
			$script=~s/^\s*//g;
			$do{$name}=$script;
			$do{$name .'.original'}=$dir .'/' .$name .'.original';
		}
	}
	close(IN);
}


if (open(OUT,">$do{$FORM{'name'}}")) {
	print OUT $FORM{'action'};	
	close(OUT);
	print "ok\n";
} else {
	print "error:Can't open file $do{$FORM{'name'}} to write\n";
}
