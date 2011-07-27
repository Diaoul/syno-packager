#!/usr/bin/perl
print "Content-type: text/html\n\n";

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

if (open(IN,'configfiles.txt')) { 
	while(<IN>) {
		chop();
		if ((!(/^#/))&&(/,/)) { 
			($script,$name)=/([^,]+),([^,]+)/;
			$script=~s/^\s*//;
			$name=~s/^\s*//;
			$do{$name}=$script;
			$do{$name .'.original'}=$dir .'/' .$name .'.original';
		}
	}
	close(IN);
}
$do{'Config File Editor'}=$dir .'/' .'configfiles.txt';
$do{'Config File Editor.original'}=$dir .'/' .'Config File Editor.original';

close(IN);
$_=$ENV{'QUERY_STRING'};
s/\%20/ /g;
($action)=/action=([^&]+)/;
if (open (IN,$do{$action})) {
	while(<IN>) {
		print;
	}
	close(IN);
} 
