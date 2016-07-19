#!/usr/local/cpanel/3rdparty/bin/perl
# Copyright 2017 Jose Pedro Andres
# URL: https://github.com/macklus/cpanel-whm-mail-outgoing-ips
# Email: macklus@debianitas.net

use Cpanel::Form            ();
use Whostmgr::ACLS          ();
use Cpanel::SafeFile        ();
use Cpanel::Rlimit          ();
use Cpanel::PublicAPI       (); 
use IPC::Open3;
use Data::Dumper;


#use Sys::Hostname qw(hostname);
#use IPC::Open3;
#use File::Basename;
#use lib '/usr/local/cpanel';
#use Cpanel::cPanelFunctions ();
#use Cpanel::Config          ();
#use Cpanel::Version::Tiny   ();

my $api = new Cpanel::PublicAPI(usessl => 0, user => 'root', accesshash => _read_hash());
my %mailhelo;
my %mailips;
my %userdomains;
my %userdatadomains;
my $domain;
my @ips = get_ips();
my ( $k, $input, $input_label, $oip, $oip_label, $helo, $helo_label );
my $changes = 0;

my %FORM = Cpanel::Form::parseform();

print "Content-type: text/html\r\n\r\n";

Whostmgr::ACLS::init_acls();
if (!Whostmgr::ACLS::hasroot()) {
    print "You do not have access to this option.\n";
#    exit();
}

Cpanel::Rlimit::set_rlimit_to_infinity();

do_head();
%mailhelo = get_hash_for_file('/etc/mailhelo');
%mailips = get_hash_for_file('/etc/mailips');
%userdomains = get_hash_for_file('/etc/userdomains');
%userdatadomains = get_userdatadomains();

foreach $k( keys %FORM ) {
    if( $k =~ /^selected_(.*)$/ ) {
        $changes++;
        $input = $1;
        $oip_label = "oip_$input";
        $oip = $FORM{$oip_label};
        $helo_label = "helo_$input";
        $helo = $FORM{$helo_label};

        $mailips{$input} = $oip;
        if( $helo ne '' ) {
            $mailhelo{$input} = $helo;
        }
    }
}

save_hash_to_file("/etc/mailips", %mailips);
save_hash_to_file("/etc/mailhelo", %mailhelo);

#print Dumper(%FORM);

print '<h2>Outgoing email IPs</h2>';
print '<p class="bg-success success-msg">Changes sucesfully commited</p>' if( $changes > 0);
print '<form method="post" action="">';
print '<table class="table table-striped">';
print ' <thead>';
print '<tr><td>&nbsp;</td><td>Domain</td><td>User</td><td>Reseller</td><td>Outgoing IP</td><td>HELO</td></tr>';
print ' </thead>';
print ' </tbody>';

foreach $domain ( sort keys %userdomains ) {
    next if( $domain eq '*' );
    print '<tr>';
    print '<td><input type="checkbox" name="selected_'.$domain.'"></td>';
    print '<td>'.$domain.'</td>';
    print '<td>'.(defined($userdomains{$domain}) ? $userdomains{$domain} : "unknow").'</td>';
    print '<td>'.(defined($userdatadomains{$domain}{'reseller'}) ? $userdatadomains{$domain}{'reseller'} : "unknow" ).'</td>';
    print '<td>'; do_outgoing_select($domain); print '</td>';
    print '<td>'; do_outgoing_helo($domain);   print '</td>';
    print '</tr>';
}

print '</tbody>';
print '</table>';
print '<input type="submit" class="btn btn-primary" value="Send">';
print '</form>';

end_head();
#
# Works end
#

sub save_hash_to_file {
    my($file, %data) = @_;

    my $out = Cpanel::SafeFile::safeopen( $fh, '>', $file );
    foreach( keys %data ) {
        print $fh "$_: $data{$_}\n";
        #print "Guardo en $file : $_ $data{$_}\n";
    }
    Cpanel::SafeFile::safeclose($fh, $out);
}

sub do_outgoing_helo {
    my $d = shift;
    print '<input type="text" name="helo_'.$d.'" class="form-control" value="';
    if( defined($mailhelo{$d})) {
        print $mailhelo{$d};
    }
    print '">';
}

sub do_outgoing_select {
    my $d = shift;
    print '<select class="form-control" name="oip_'.$d.'">';
    foreach(@ips) {
        if( defined($mailips{$d}) && $mailips{$d} eq $_ ) {
            print '<option selected>'.$_.'</option>';
        } else {
            print '<option>'.$_.'</option>';
        }
    }
    print '</select>';
}

sub get_ips {
    my $ref = $api->whm_api('listips');
    my @data;

    foreach( @{$ref->{data}{ip}} ) {
        next if ( $_->{ip} eq '127.0.0.1' );
        push( @data, $_->{ip} );
    }
    return @data;
    
}


sub _read_hash() {
    my $AccessHash = "/root/.accesshash";

    eval {
        unless ( -f $AccessHash )
        {
            my $pid = IPC::Open3::open3( my $wh, my $rh, my $eh,
                '/usr/local/cpanel/whostmgr/bin/whostmgr setrhash' );
            waitpid( $pid, 0 );
        }
    };
    open( my $hash_fh, "<", $AccessHash ) || die "Cannot open access hash: " . $AccessHash;

    my $accesshash = do { local $/; <$hash_fh>; };
    $accesshash =~ s/\n//g;
    close($hash_fh);

    return $accesshash;
}

sub get_hash_for_file {
    my $file = shift;
    my %d = ();    
    if ( -e $file ) {
        my $inlock = Cpanel::SafeFile::safeopen(\*IN,"<","$file");
        my @data = <IN>;
        Cpanel::SafeFile::safeclose(\*IN,$inlock);

        foreach( @data ) {
            chomp;
            if( /(.*): (.*)/ ) {
                $d{$1} = $2;
            }
        }
    }
    return %d;
}

sub get_userdatadomains {
    my %d = {};
    my $inlock = Cpanel::SafeFile::safeopen(\*IN,"<","/etc/userdatadomains");
    my @data = <IN>;
    Cpanel::SafeFile::safeclose(\*IN,$inlock);
    foreach( @data ) {
        chomp;
        if( /(.*): (.*)==(.*)==(.*)==(.*)==(.*)==(.*)==(.*)==(.*)==0/ ) {
            $d{$1}{'domain'} = $1;
            $d{$1}{'user'} = $2;
            $d{$1}{'reseller'} = $3;
            $d{$1}{'type'} = $4;
            $d{$1}{'main_domain'} = $5;
            $d{$1}{'home'} = $6;
            $d{$1}{'ip_hosts'} = $7;
        }
    }
    return %d;
}

sub do_head {
 print <<'DO_HEADER';
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Exim Outgoing IP config</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css" crossorigin="anonymous">
    <style type="text/css">
    .success-msg {
        padding: 30px;
        marging: 30px;
    }
    </style>
</head>
<body>
    <div class="container">
DO_HEADER
}

sub end_head {
    print <<'END_HEADER';
    </div> <!-- /container -->
</body>
</html>
END_HEADER
}

1;
