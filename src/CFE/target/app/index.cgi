#!/usr/bin/perl
use File::Copy;

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
$dir=~s#/[^/]+$##g; #

sub addCfgFile {
	($fname,$name)=@_;
	$fname=~s/^\s*//g;
	$name=~s/^\s*//g;
	if ($tmpljs{'names'}) {
		$tmpljs{'names'}.=',';
	}
	$tmpljs{'names'}.="'" .$name ."'" ;
	$path=$dir .'/' .$name .'.original';
	if (!( -r $path)){
		copy($fname,$path);
	}
}

$gotown=0;
if (open(IN,"configfiles.txt")) {
	while(<IN>) {
		chop();
		if ((!(/^#/))&&(/,/)) {
			($fname,$name)=/([^,]+),(.*)/;
			addCfgFile($fname,$name);
		}
	}
}

addCfgFile($dir .'/' .'configfiles.txt', 'Config File Editor');

# get javascript
$js="";
if (open(IN,"script.js")) {
	while (<IN>) {
		s/==:([^:]+):==/$tmpljs{$1}/g;
		$js.=$_;
	}
	close(IN);
}


$tmplhtml{'javascript'}=$js;
$tmplhtml{'debug'}=$debug;

# print html page
if (open(IN,"page.html")) {
	while (<IN>) {
		s/==:([^:]+):==/$tmplhtml{$1}/g;
		print $_;
	}
	close(IN);
}
