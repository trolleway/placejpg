
SYSTEM=Q4273280 #moscowbus
SYSTEM=Q122992634 #Tver
SYSTEM=FROMFILENAME #FROMFILENAME
mostroll=Q4304313
spbtroll=Q4407766
mosbus=Q4304026
spbbus=Q4407764
vitebsktroll=Q2089752
vitebskbus=Q16271696
vidnoyetroll=Q4110660
moscoblbus=Q125810299

ZIU9=Q198271
ZIU6205=Q2424761
trolza527500=Q3498797
trolza5275optima=Q4463694
trolza526405=Q131377253
trolza5265=Q3498832
trolza6206=Q4463696
BTZ527601=Q4074052
BTZ527604=Q4074053
BTZ52761=Q4074054
gorozanin=Q113409885
VZTM5284=Q21660663
PTZ210=Q123915913
PTZ5283=Q124209334
BKM101=Q4053993
BKM201=Q4053991
BKM321=Q4053996
vmz529800=Q4101956
vmz529801=Q4101953
vmz52980150=Q4101954
vmz6215=Q4101957
vmz61251=Q4101960
ktg=Q4220243
svarzmaz6275=Q4402988
svarzmaz6235=Q4402985
admiral=Q97278541
MAZ203T=Q4273304
MTRZ5279=Q4273640
ST6217M=Q4403223
skoda9tr=Q391947
YUMZT2=Q3810753
bogdanT70117=Q131372899

ikarus256=Q846220
ikarus260=Q897765
ikarus280=Q1076730
ikarus283=Q4041280
ikarus415=Q897608
ikarus435=Q718410
liaz677=Q1978784
liaz4292=Q28666158
liaz5256=Q7241301
liaz5292=Q4260755
liaz5293=Q4260759
liaz5250=Q120850767
liaz6212=Q4260761
liaz6213=Q10995629
liaz6274=Q55658359
Volgabus5270=Q4123082
Volzanin528501=Q125210480
Volgabus6270=Q16631389
VolgabusCityRhythm18=Q124130821
VolgabusCityRhythm15=Q124130919
ScaniaL94=Q13162904
ScaniaOmniLink=Q1409162
MAN_LIONCOACH_R07=Q124475008
MAZ103=Q2529337
MAZ105=Q1110246
MAZ107=Q4273277
MAZ203=Q1964501
MAZ206=Q4273280
MARZ52661=Q130462996
MercedesBenz0303=Q1509048
MercedesBenz0325=Q4044005
MercedesBenzConnecto=Q1921228
MercedesBenzO307=Q1495394
MercedesBenzO305G=Q11777426

NEFAZ5299=Q4318022
PAZ3205=Q1997344
GAZELLE=Q650464
MercedesVario=Q1921351
MercedesShpurbus=Q1921285
nefaz529940=Q118270591
kamaz6282=Q60851127
golaz6228_3axle=Q4141289
PAZ3205=Q1997344
PAZ3237=Q2043741
FIAT_Ducato_244=Q125203938
VDL_Citea_SLE_120=Q125210502
YaAZ_5267=Q4535783
DaewooBS=Q12591646
Bychok=Q15942199
FordTransit2013=Q130361067
GolazAKA6226=Q4141293
LAZ695N=Q130810177
LAZ695T=Q130851629


MODE='full'

if [ $MODE = "full" ]; then
# switchoff  this
city=blagoveshchensk
SYSTEM=Q130375300
python3 vehicle-upload.py -v bus  --system $SYSTEM  --model $liaz5292   i/_buses/$city/liaz5292 --number BEFORE_UNDERSCORE  --country countries.gpkg  --progress --street trolleybus.gpkg
fi 

if [ $MODE = "full" ]; then
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $ZIU9   i/_trolleybuses/moscow/ZIU9  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $ZIU6205   i/_trolleybuses/moscow/ZIU6205  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 

#moscow
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $vmz529801   i/_trolleybuses/moscow/vmz529801  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $vmz61251   i/_trolleybuses/moscow/vmz61251  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $svarzmaz6275   i/_trolleybuses/moscow/svarzmaz6275  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $svarzmaz6235   i/_trolleybuses/moscow/svarzmaz6235  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $trolza5275optima   i/_trolleybuses/moscow/trolza5275optima  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $trolza5265   i/_trolleybuses/moscow/trolza5265  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $trolza6206   i/_trolleybuses/moscow/trolza6206  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $BKM101   i/_trolleybuses/moscow/BKM101  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $BKM201   i/_trolleybuses/moscow/BKM201  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $BKM321   i/_trolleybuses/moscow/BKM321  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $MTRZ5279   i/_trolleybuses/moscow/MTRZ5279  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 

#moscow-rare
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $VZTM5284   i/_trolleybuses/moscow/rare/VZTM5284  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $ktg   i/_trolleybuses/moscow/ktg  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $trolza527500   i/_trolleybuses/moscow/rare/trolza527500  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $BTZ527601   i/_trolleybuses/moscow/rare/BTZ527601  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $BTZ52761   i/_trolleybuses/moscow/rare/BTZ52761  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $YUMZT2   i/_trolleybuses/moscow/rare/YUMZT2  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $mostroll  --model $skoda9tr   i/_trolleybuses/moscow/rare/skoda9tr  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 

#vidnoye
city=vidnoye 
python3 vehicle-upload.py -v trolleybus --system $vidnoyetroll  --model $vmz529800   i/_trolleybuses/vidnoye/vmz529800  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $vidnoyetroll  --model $ZIU9   i/_trolleybuses/vidnoye/ZIU9  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $vidnoyetroll  --model $trolza526405   i/_trolleybuses/vidnoye/trolza526405  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $vidnoyetroll  --model $bogdanT70117   i/_trolleybuses/vidnoye/bogdanT701.17  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $vidnoyetroll  --model $trolza5275optima   i/_trolleybuses/$city/trolza5275optima  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $vidnoyetroll  --model $MAZ206   i/_trolleybuses/$city/MAZ206  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
# podolsk
SYSTEM=Q4368068
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $ZIU9   i/_trolleybuses/podolsk/ZIU9  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 




SYSTEM=Q4112970 #ekaterinburg_troll
city=vladivostok 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $ZIU9   i/_trolleybuses/$city/ZIU9  --number BEFORE_UNDERSCORE   --progress --country "Primorsky Krai"  --street trolleybus.gpkg 


SYSTEM=Q4174323 #ekaterinburg_troll
city=ekaterinburg
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $BKM321   i/_trolleybuses/$city/BKM321  --number BEFORE_UNDERSCORE --country "Sverdlovsk Oblast"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $ZIU9   i/_trolleybuses/$city/ZIU9  --number BEFORE_UNDERSCORE --country "Sverdlovsk Oblast"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $BTZ527604   i/_trolleybuses/$city/BTZ527604  --number BEFORE_UNDERSCORE --country "Sverdlovsk Oblast"  --progress --street trolleybus.gpkg 

SYSTEM=Q4407766 #spb_troll
city=spb
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $PTZ210   i/_trolleybuses/cities/$city/PTZ210  --number BEFORE_UNDERSCORE --country "Saint Petersburg"  --progress --street trolleybus.gpkg 
#python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $PTZ5283   i/_trolleybuses/cities/$city/PTZ5283  --number BEFORE_UNDERSCORE --country "Saint Petersburg"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $ZIU9   i/_trolleybuses/cities/$city/ZIU-9  --number BEFORE_UNDERSCORE --country "Saint Petersburg"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $VZTM5284#ziu-9   i/_trolleybuses/cities/$city/VZTM5284  --number BEFORE_UNDERSCORE --country "Saint Petersburg"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $ZIU6205   i/_trolleybuses/cities/$city/ZIU6205  --number BEFORE_UNDERSCORE --country "Saint Petersburg"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $trolza5265   i/_trolleybuses/cities/$city/trolza5265  --number BEFORE_UNDERSCORE --country "Saint Petersburg"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $vmz529800   i/_trolleybuses/cities/$city/vmz529800  --number BEFORE_UNDERSCORE --country "Saint Petersburg"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $vmz529801   i/_trolleybuses/cities/$city/vmz529801  --number BEFORE_UNDERSCORE --country "Saint Petersburg"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $vmz52980150   i/_trolleybuses/cities/$city/vmz52980150  --number BEFORE_UNDERSCORE --country "Saint Petersburg"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $trolza5275optima   i/_trolleybuses/cities/$city/trolza5275optima  --number BEFORE_UNDERSCORE --country "Saint Petersburg"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $BTZ527604   i/_trolleybuses/cities/$city/BTZ527604  --number BEFORE_UNDERSCORE --country "Saint Petersburg"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $vmz6215   i/_trolleybuses/cities/$city/vmz6215  --number BEFORE_UNDERSCORE --country "Saint Petersburg"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $BKM101   i/_trolleybuses/cities/$city/BKM101  --number BEFORE_UNDERSCORE --country "Saint Petersburg"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $BKM201   i/_trolleybuses/cities/$city/BKM201  --number BEFORE_UNDERSCORE --country "Saint Petersburg"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $BKM321   i/_trolleybuses/cities/$city/BKM321  --number BEFORE_UNDERSCORE --country "Saint Petersburg"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $ktg   i/_trolleybuses/cities/$city/ktg  --number BEFORE_UNDERSCORE --country "Saint Petersburg"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model Q4535800   i/_trolleybuses/cities/$city/yatb1  --number BEFORE_UNDERSCORE --country "Saint Petersburg"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $admiral   i/_trolleybuses/cities/$city/admiral  --number BEFORE_UNDERSCORE --country "Saint Petersburg"  --progress --street trolleybus.gpkg 


SYSTEM=Q4078421 #barnaul_troll
city=barnaul
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $vmz529800   i/_trolleybuses/$city/vmz529800  --number BEFORE_UNDERSCORE --country "Altai Krai"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $ZIU9   i/_trolleybuses/$city/ziu9  --number BEFORE_UNDERSCORE --country "Altai Krai"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $BKM201   i/_trolleybuses/$city/BKM201  --number BEFORE_UNDERSCORE --country "Altai Krai"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $vmz52980150   i/_trolleybuses/$city/vmz52980150  --number BEFORE_UNDERSCORE --country "Altai Krai"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $ST6217M   i/_trolleybuses/$city/ST6217M  --number BEFORE_UNDERSCORE --country "Altai Krai"  --progress --street trolleybus.gpkg 


SYSTEM=Q4497754 #khimki_troll
city=khimki
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $ZIU9   i/_trolleybuses/$city/ziu9  --number BEFORE_UNDERSCORE --country countries.gpkg --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $BKM101   i/_trolleybuses/$city/BKM101  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $BKM321   i/_trolleybuses/$city/BKM321  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $vmz52980150   i/_trolleybuses/$city/vmz52980150  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 


SYSTEM=Q4406433 #samara_troll
city=samara
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $ZIU9   i/_trolleybuses/$city/ziu9  --number BEFORE_UNDERSCORE --country countries.gpkg --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $BKM101   i/_trolleybuses/$city/BKM101  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $BTZ527604   i/_trolleybuses/$city/BTZ527604  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 

SYSTEM=Q4494362 #khabarovsk_troll
city=khabarovsk
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $gorozanin   i/_trolleybuses/$city/gorozanin  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $BKM321   i/_trolleybuses/$city/BKM321  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $vmz529800   i/_trolleybuses/$city/vmz529800  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $trolza5275optima   i/_trolleybuses/$city/trolza5275optima  --number BEFORE_UNDERSCORE --country countries.gpkg  --progress --street trolleybus.gpkg 





SYSTEM=Q4402672 #ryazan_troll
city=ryazan
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $VZTM5284   i/_trolleybuses/$city/pig  --number BEFORE_UNDERSCORE --country "Ryazan Oblast"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $MAZ203T   i/_trolleybuses/$city/MAZ203T  --number BEFORE_UNDERSCORE --country "Ryazan Oblast"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $ZIU9   i/_trolleybuses/$city/ZIU9  --number BEFORE_UNDERSCORE --country "Ryazan Oblast"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $vmz529800   i/_trolleybuses/$city/vmz529800  --number BEFORE_UNDERSCORE --country "Ryazan Oblast"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $vmz529801   i/_trolleybuses/$city/vmz529801  --number BEFORE_UNDERSCORE --country "Ryazan Oblast"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $vmz52980150   i/_trolleybuses/$city/vmz52980150  --number BEFORE_UNDERSCORE --country "Ryazan Oblast"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $admiral   i/_trolleybuses/$city/admiral  --number BEFORE_UNDERSCORE --country "Ryazan Oblast"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $trolza5265   i/_trolleybuses/$city/trolza5265  --number BEFORE_UNDERSCORE --country "Ryazan Oblast"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v trolleybus --system $SYSTEM  --model $trolza5265   i/_trolleybuses/$city/trolza5265  --number BEFORE_UNDERSCORE --country "Ryazan Oblast"  --progress --street trolleybus.gpkg 



fi

python3 vehicle-upload.py -v bus --system $mosbus  --model $kamaz6282   i/_buses/moscow/mgt_kamaz6282 --country countries.gpkg --number BEFORE_UNDERSCORE   --progress  --operator-vehicle-category "Mosgortrans buses" --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $liaz5256   i/_buses/moscow/mgt_liaz5256 --country countries.gpkg --number BEFORE_UNDERSCORE   --progress  --operator-vehicle-category "Mosgortrans buses" --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $liaz6212   i/_buses/moscow/mgt_liaz6212 --country countries.gpkg --number BEFORE_UNDERSCORE --operator-vehicle-category "Mosgortrans buses"   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $liaz6213   i/_buses/moscow/mgt_liaz6213 --country countries.gpkg --number BEFORE_UNDERSCORE --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $liaz6274   i/_buses/moscow/mgt_liaz6274 --country countries.gpkg --number BEFORE_UNDERSCORE --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $MAZ103   i/_buses/moscow/mgt_maz103 --country countries.gpkg --number BEFORE_UNDERSCORE --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $MAZ107   i/_buses/moscow/mgt_maz107 --country countries.gpkg --number BEFORE_UNDERSCORE --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $golaz6228_3axle   i/_buses/moscow/mgt_golaz6228_3axle --country countries.gpkg --number BEFORE_UNDERSCORE --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $PAZ3237   i/_buses/moscow/mgt_PAZ3237 --country countries.gpkg --number BEFORE_UNDERSCORE --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $MercedesBenzConnecto   i/_buses/moscow/mgt_MercedesBenzConnecto --country countries.gpkg --number BEFORE_UNDERSCORE  --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $Volgabus6270   i/_buses/moscow/mgt_Volgabus6270 --country countries.gpkg --number BEFORE_UNDERSCORE  --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 

python3 vehicle-upload.py -v bus --system $mosbus  --model $Volgabus5270   i/_buses/moscow/mgt_Volgabus5270 --country countries.gpkg --number BEFORE_UNDERSCORE  --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $nefaz529940   i/_buses/moscow/mgt_nefaz529940 --country countries.gpkg --number BEFORE_UNDERSCORE   --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $liaz5292   i/_buses/moscow/mgt_liaz5292 --country countries.gpkg --number BEFORE_UNDERSCORE    --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $liaz5292   i/_buses/moscow/tmp20_liaz5292 --country countries.gpkg --number BEFORE_UNDERSCORE  --operator-vehicle-category "TMP20 buses"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $MAN_LIONCOACH_R07   i/_buses/moscow/MAN_LIONCOACH_R07 --country countries.gpkg --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $MAZ203   i/_buses/moscow/avtoline_MAZ203 --country countries.gpkg --number BEFORE_UNDERSCORE  --operator-vehicle-category "Avtoline buses in Moscow"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $FordTransit2013   i/_buses/moscow/FordTransit2013 --country countries.gpkg --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 

#rare
if [ $MODE = "full" ]; then

python3 vehicle-upload.py -v bus --system $mosbus  --model $liaz4292   i/_buses/moscow/mgt_liaz4292 --country countries.gpkg --number BEFORE_UNDERSCORE   --progress  --operator-vehicle-category "Mosgortrans buses" --street trolleybus.gpkg 

python3 vehicle-upload.py -v bus --system $mosbus  --model $liaz677   i/_buses/moscow/mgt_liaz677 --country countries.gpkg --number BEFORE_UNDERSCORE   --progress  --operator-vehicle-category "Mosgortrans buses" --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $liaz5293   i/_buses/moscow/mgt_liaz5293 --country countries.gpkg --number BEFORE_UNDERSCORE   --progress  --operator-vehicle-category "Mosgortrans buses" --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $YaAZ_5267   i/_buses/moscow/mgt_YaAZ_5267 --country countries.gpkg --number BEFORE_UNDERSCORE   --progress  --operator-vehicle-category "Mosgortrans buses" --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $MAZ203   i/_buses/moscow/MAZ203 --country countries.gpkg --number BEFORE_UNDERSCORE   --progress  --operator-vehicle-category "Mosgortrans buses" --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $GAZELLE   i/_buses/moscow/mgt_GAZELLE --country countries.gpkg --number BEFORE_UNDERSCORE   --progress  --operator-vehicle-category "Mosgortrans buses" --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $Bychok   i/_buses/moscow/mgt_Bychok --country countries.gpkg --number BEFORE_UNDERSCORE   --progress  --operator-vehicle-category "Mosgortrans buses" --street trolleybus.gpkg 
#python3 vehicle-upload.py -v bus --system $mosbus  --model $VDL_Citea_SLE_120   i/_buses/moscow/VDL_Citea_SLE_120 --country countries.gpkg --number BEFORE_UNDERSCORE    --progress --street trolleybus.gpkg 
#python3 vehicle-upload.py -v bus --system $mosbus  --model $Volzanin528501   i/_buses/moscow/mgt_Volzanin528501 --country countries.gpkg --number BEFORE_UNDERSCORE  --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $MercedesBenz0325   i/_buses/moscow/mgt_MercedesBenz0325 --country countries.gpkg --number BEFORE_UNDERSCORE  --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $ikarus415   i/_buses/moscow/mgt_ikarus415 --country countries.gpkg --number BEFORE_UNDERSCORE  --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 

python3 vehicle-upload.py -v bus --system $mosbus  --model $ikarus435   i/_buses/moscow/mgt_ikarus435 --country countries.gpkg --number BEFORE_UNDERSCORE  --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $ikarus260   i/_buses/moscow/mgt_ikarus260 --country countries.gpkg --number BEFORE_UNDERSCORE    --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $ikarus280   i/_buses/moscow/mgt_ikarus280 --country countries.gpkg --number BEFORE_UNDERSCORE  --operator-vehicle-category "Mosgortrans buses" --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $ikarus283   i/_buses/moscow/mgt_ikarus283 --country countries.gpkg --number BEFORE_UNDERSCORE  --operator-vehicle-category "Mosgortrans buses" --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $FIAT_Ducato_244   i/_buses/moscow/mgt_FIAT_Ducato_244 --country countries.gpkg --number BEFORE_UNDERSCORE  --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $MARZ52661   i/_buses/moscow/mgt_MARZ52661 --country countries.gpkg --number BEFORE_UNDERSCORE  --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $GolazAKA6226   i/_buses/moscow/mgt_GolazAKA6226 --country countries.gpkg --number BEFORE_UNDERSCORE  --operator-vehicle-category "Mosgortrans buses"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $mosbus  --model $MAZ206   i/_buses/moscow/MAZ206 --country countries.gpkg --number BEFORE_UNDERSCORE    --progress --street trolleybus.gpkg 
fi


SYSTEM=Q16271701
city=ryazan
python3 vehicle-upload.py -v bus --system $SYSTEM  --model $liaz5292   i/_buses/ryazan/liaz5292 --country "Ryazan Oblast" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 

SYSTEM=Q128214955
city=Vidnoe
python3 vehicle-upload.py -v bus --system $SYSTEM  --model $liaz5256   i/_buses/$city/liaz5256 --country countries.gpkg --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $SYSTEM  --model $MercedesShpurbus   i/_buses/$city/MercedesShpurbus --country countries.gpkg --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 

python3 vehicle-upload.py -v bus --system $spbbus  --model Q124130334#SetraS215HD   i/_buses/spb/SetraS215HD --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $liaz6213  i/_buses/spb/Passazhiravtotrans_liaz6213  --operator-vehicle-category "Passazhiravtotrans" --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $VolgabusCityRhythm18  i/_buses/spb/Passazhiravtotrans_VolgabusCityRhythm18 --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $VolgabusCityRhythm15  i/_buses/spb/Passazhiravtotrans_VolgabusCityRhythm15  --operator-vehicle-category "Passazhiravtotrans" --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $ScaniaOmniLink  i/_buses/spb/ScaniaOmniLink --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $MAZ103  i/_buses/spb/MAZ103 --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $MAZ203  i/_buses/spb/MAZ203 --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $MAZ206  i/_buses/spb/MAZ206 --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $MercedesBenz0303  i/_buses/spb/MercedesBenz0303 --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $NEFAZ5299  i/_buses/spb/Passazhiravtotrans_NEFAZ5299  --operator-vehicle-category "Passazhiravtotrans" --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
#spb-historical
python3 vehicle-upload.py -v bus --system $spbbus  --model $liaz6212  i/_buses/spb/liaz6212 --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $liaz5256  i/_buses/spb/liaz5256 --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $liaz5293  i/_buses/spb/Piteravto_liaz5293  --operator-vehicle-category "Piteravto" --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $Volgabus5270  i/_buses/spb/Passazhiravtotrans_Volgabus5270   --operator-vehicle-category "Passazhiravtotrans" --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $Volgabus6270  i/_buses/spb/Volgabus6270 --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $ikarus256  i/_buses/spb/ikarus256 --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $ikarus280  i/_buses/spb/ikarus280 --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $ikarus435  i/_buses/spb/ikarus435 --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $ScaniaL94  i/_buses/spb/ScaniaL94 --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $PAZ3205  i/_buses/spb/PAZ3205 --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $liaz5292  i/_buses/spb/liaz5292 --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $GAZELLE  i/_buses/spb/GAZELLE --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $spbbus  --model $MercedesVario  i/_buses/spb/MercedesVario --country "Saint Petersburg" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 

city=vitebsk
python3 vehicle-upload.py -v bus --system $vitebskbus  --model $MAZ103  i/_buses/$city/MAZ103 --country "Belarus" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $vitebskbus  --model $MAZ105  i/_buses/$city/MAZ105 --country "Belarus" --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 

vyborgbus=Q4128546
city=Vyborg
python3 vehicle-upload.py -v bus --system $vyborgbus --city $city --model $ScaniaOmniLink  i/_buses/vyborg/ScaniaOmniLink --country countries.gpkg --number BEFORE_UNDERSCORE   --progress --street trolleybus.gpkg 




city="Moscow Oblast"


python3 vehicle-upload.py -v bus --system $moscoblbus --city "Q1697" --model $liaz5292  i/_buses/mostransavto/liaz5292 --country countries.gpkg --number BEFORE_UNDERSCORE  --operator-vehicle-category "Mostransavto"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $moscoblbus --city "Q1697" --model $NEFAZ5299  i/_buses/mostransavto/NEFAZ5299 --country countries.gpkg --number BEFORE_UNDERSCORE  --operator-vehicle-category "Mostransavto"  --progress --street trolleybus.gpkg 
python3 vehicle-upload.py -v bus --system $moscoblbus --city "Q1697" --model $NEFAZ5299  i/_buses/mostransavto_nonum/NEFAZ5299 --country countries.gpkg  --operator-vehicle-category "Mostransavto"  --progress --street trolleybus.gpkg 

city=Yekaterinburg
ekaterinburgbus=Q4174307
python3 vehicle-upload.py -v bus --system $ekaterinburgbus  --model $nefaz529940   i/_buses/ekaterinburg/nefaz529940 --country countries.gpkg --number BEFORE_UNDERSCORE    --progress --street trolleybus.gpkg

city=Nakhodka
nakhodkabus=Q4314733
python3 vehicle-upload.py -v bus --system $nakhodkabus  --model $DaewooBS   i/_buses/nakhodka/DaewooBS --number BEFORE_UNDERSCORE  --country countries.gpkg  --progress --street trolleybus.gpkg

city=Samara
SYSTEM=Q4406397
python3 vehicle-upload.py -v bus --system $SYSTEM  --model $PAZ3205   i/_buses/$city/PAZ3205 --number BEFORE_UNDERSCORE  --country countries.gpkg  --progress --street trolleybus.gpkg


city=Barnaul
SYSTEM=Q4078392
python3 vehicle-upload.py -v bus --system $SYSTEM  --model $ScaniaOmniLink   i/_buses/$city/ScaniaOmniLink --number BEFORE_UNDERSCORE  --country countries.gpkg  --progress --street trolleybus.gpkg




python3 auto-upload.py -v bus   i/_buses/no_fleetnum/liaz5256  --country countries.gpkg  --progress --street trolleybus.gpkg --model $liaz5256
python3 auto-upload.py -v bus   i/_buses/no_fleetnum/liaz677  --country countries.gpkg  --progress --street trolleybus.gpkg --model $liaz677
python3 auto-upload.py -v bus   i/_buses/no_fleetnum/liaz5250  --country countries.gpkg  --progress --street trolleybus.gpkg --model $liaz5250
python3 auto-upload.py -v bus   i/_buses/no_fleetnum/liaz5292  --country countries.gpkg  --progress --street trolleybus.gpkg --model $liaz5292
python3 auto-upload.py -v bus   i/_buses/no_fleetnum/liaz6212  --country countries.gpkg  --progress --street trolleybus.gpkg --model $liaz6212
python3 auto-upload.py -v bus   i/_buses/no_fleetnum/MercedesBenzO307_round_short  --country countries.gpkg  --progress --street trolleybus.gpkg --model $MercedesBenzO307
python3 auto-upload.py -v bus   i/_buses/no_fleetnum/MercedesBenzO305G_round_long  --country countries.gpkg  --progress --street trolleybus.gpkg --model $MercedesBenzO305G
python3 auto-upload.py -v bus   i/_buses/no_fleetnum/LAZ695N_90s  --country countries.gpkg  --progress --street trolleybus.gpkg --model $LAZ695N
python3 auto-upload.py -v bus   i/_buses/no_fleetnum/LAZ695T_90s  --country countries.gpkg  --progress --street trolleybus.gpkg --model $LAZ695T