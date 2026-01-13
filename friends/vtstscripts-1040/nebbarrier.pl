#!/usr/bin/env perl
#;-*- Perl -*-

use FindBin qw($Bin);
use lib "$Bin";
use Vasp;
use Data::Dumper qw(Dumper);

open NEB , ">neb.dat" ;

@args = @ARGV;
@alg_args;
foreach my $k (@args) {
    if (index($k,"-") != -1) { #want to separate options preceded with "-"
        push @alg_args, shift(@args);
    }
}
if (@args==0) {
    opendir(DIR,".") or die "couldn't open . ($!)\n";
    @list = readdir(DIR);
    closedir(DIR);

    @directories = grep {-d && /^[0-9][0-9]$/i} @list;
    @directories = sort {$a<=>$b} @directories;
} else {
    @directories = @args;
}
#  check for ssneb
$ssneb_flag = `grep 'LNEBCELL' 01/OUTCAR|tail -1`;
@ssneb_flag = split(/\s+/,$ssneb_flag);
$ssneb_flag = $ssneb_flag[@ssneb_flag-1];
$nions = `grep 'NIONS' 01/OUTCAR|tail -1`;
@nions = split(/\s+/,$nions);
$nions = $nions[@nions-1];
$nions_more = $nions+1;

if ($ssneb_flag =~ /T/){
    open NEBSS , ">nebss.dat" ;
    #print "$ssneb_flag \n";
}
  
#  print "#Directories found: ".join(" ",@directories)."\n";

sub ForceTan{
				$dir = shift;
				@frozen = @_;
    my @force_tot = split(/\n/,`grep 'TOTAL-FORCE (eV/Angst)' -A $nions_more $dir/OUTCAR|tail -$nions`); #grab forces on final image
    my @force_3d;
    foreach my $a ( 0 .. $#force_tot) { #fill up matrix with force values (N x 3)
        my @f_row = split(/\s+/,$force_tot[$a]);
								@f_row = @f_row[4,5,6];
								if (grep /^$a$/, @frozen) {
									   @f_row = (0,0,0);
								}
        foreach my $b ( 0 .. 2) {
            $force_3d[$a][$b] = $f_row[$b];
        }
    }
				return \@force_3d;
}

$dist_cum = 0;
for ($i=0; $i<@directories; $i++) {
    (-e "$directories[$i]/OUTCAR") || die "No OUTCAR in $directories[$i]!\n";

    $energy = `grep 'energy  w' $directories[$i]/OUTCAR|tail -1`;
#    $dist = `grep 'NEB: distance' $directories[$i]/OUTCAR|tail -1`;
    $force = `grep 'NEB: projections' $directories[$i]/OUTCAR|tail -1`;
    if ($ssneb_flag =~ /T/){
        $force = `grep 'NEBCELL: projections' $directories[$i]/OUTCAR|tail -1`;
    };
    $energy =~ s/\s+$//g;
    @energy = split(/\s+/,$energy);
    $energy = $energy[@energy-1];

    if ($i==0) { $energy0 = $energy; }
    $energy -= $energy0;

    if ($i>0) {
        if (-e "$directories[$i]/CONTCAR") {
            $file1 = "$directories[$i]/CONTCAR";
        } else {
            $file1 = "$directories[$i]/POSCAR";
        }
        if (-e "$directories[$i-1]/CONTCAR") {
            $file2 = "$directories[$i-1]/CONTCAR";
        } else {
            $file2 = "$directories[$i-1]/POSCAR";
        }
        $dist = `$Bin/dist.pl $file1 $file2`; # distance calculated using square root of sum of squared difference in coordinates
        if (grep /-alt_dist/,@alg_args) { # get distance by projecting displacement vector along force vector
								    my $diffcon_raw = `$Bin/diffcon.pl $file1 $file2`;
            my @diffcon_raw = split(/\n/,$diffcon_raw);
            my @diffcon;
												my @frozenAtoms = ();
            foreach my $n ( 0 .. $nions-1) {
                my @diffcon_n = split(/\s+/,$diffcon_raw[$n]);
                foreach my $m ( 0 .. 2) {
                    if (index($diffcon_n[0], "-") != -1) {
                        $diffcon[$n][$m] = @diffcon_n[$m];
                    } else {
                        $diffcon[$n][$m] = @diffcon_n[$m+1];
                    }
                }
																if ($diffcon[$n][0] == $diffcon[$n][1] and $diffcon[$n][1] == $diffcon[$n][2] and $diffcon[$n][0] == 0) {
																				push @frozenAtoms, $n;
																}				
            }
				        @force_i = ForceTan($directories[$i],@frozenAtoms); # forces on current image
    				    @force_prev = ForceTan($directories[$i-1],@frozenAtoms); # forces on previous image
            @force_sum = vsum(@force_i,@force_prev,$nions);
            @force_avg = vmult(@force_sum,0.5,$nions);
            @unit_favg = unit(@force_avg,$nions);
            $dist = abs(dot_product(@unit_favg,\@diffcon,$nions)); #distance along direction of force vector b/w images
        }
        if ($ssneb_flag =~ /T/){
            if($i == @directories-1){ 
            $dist = $dist1[@dist1-2];
            } else{
            $dist1 = `grep 'NEBCELL: distance' $directories[$i]/OUTCAR|tail -1`;
            @dist1 = split(/\s+/,$dist1);
            $dist = $dist1[@dist1-3];}
        }
    } else {
       $dist = 0;
    }
				print "$dist\n";

    @force = split(/\s+/,$force);
    $force = $force[@force-1];

    $dist_cum += $dist;

    if ($ssneb_flag !~ /T/){
    # Get the coordinates to find the local tangent for the end images
    if($i == 0) {
        if (-e "$directories[$i]/CONTCAR") {
            $file1 = "$directories[$i]/CONTCAR";
        } else {
            $file1 = "$directories[$i]/POSCAR";
        }
        if (-e "$directories[$i+1]/CONTCAR") {
            $file2 = "$directories[$i+1]/CONTCAR";
        } else {
            $file2 = "$directories[$i+1]/POSCAR";
        }
        $ocar = "$directories[$i]/OUTCAR";
		# note correction: switched file1 and file2 for correct tangent direction
        $force = `$Bin/nebforces.pl $file2 $file1 $ocar`;
    } elsif($i == @directories-1) {
        if (-e "$directories[$i]/CONTCAR") {
            $file1 = "$directories[$i]/CONTCAR";
        } else {
            $file1 = "$directories[$i]/POSCAR";
        }
        if (-e "$directories[$i-1]/CONTCAR") {
            $file2 = "$directories[$i-1]/CONTCAR";
        } else {
            $file2 = "$directories[$i-1]/POSCAR";
        }
        $ocar = "$directories[$i]/OUTCAR";
        $force = `$Bin/nebforces.pl $file1 $file2 $ocar`;
    }
    }
    printf NEB "%3i %12.6f %12.6f %12.6f %3i\n",$i,$dist_cum,$energy,$force,$directories[$i];
    if ($ssneb_flag =~ /T/){
        printf NEBSS "%3i %12.6f %12.6f %12.6f %3i\n",$i,$dist_cum/sqrt($nions),$energy/$nions,$force/sqrt($nions),$directories[$i];
        }
    }
#print "nebbarrier.pl done \n";
close NEB;
if ($ssneb_flag !~ /T/){close NEBSS;}

