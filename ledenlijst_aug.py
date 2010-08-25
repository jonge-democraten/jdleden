from __future__ import print_function
import os, sys

def csvsplit(line):
  naam=""
  for key in keys.keys():
    keys[key][1]=line.split(";")[keys[key][0]].strip("\"").strip("\"\n")
  if keys['Tussenvoegsel'][1]=='':
    naam=keys['Voornaam'][1]+" "+keys['Achternaam'][1]
  else:
    naam=keys['Voornaam'][1]+" "+keys['Tussenvoegsel'][1]+" "+keys['Achternaam'][1]
#  lid=[int(keys['Lidnummer'][1]),naam,keys['Straat'][1],keys['Woonplaats'][1],keys['E-mail'][1],keys['Postcode'][1].split()]
  lid=[int(keys['Lidnummer'][1]),naam,keys['E-mail'][1]]
  return lid

def csvsplit2(line):
  naam=""
  for key in keys2.keys():
    keys2[key][1]=line.split(";")[keys2[key][0]].strip("\"").strip("\n")
  if keys['Tussenvoegsel'][1]=='':
    naam=keys2['Voornaam'][1]+" "+keys2['Achternaam'][1]
  else:
    naam=keys2['Voornaam'][1]+" "+keys2['Tussenvoegsel'][1]+" "+keys2['Achternaam'][1]
  lid=[int(keys2['Lidnummer'][1]),naam,keys2['E-mail'][1]]
  return lid
#def csvsplit2(line):
#  naam=""
#  for key in keys2.keys():
#    keys2[key][1]=line.split(",")[keys2[key][0]].strip("\"").strip("\n")
#  lid=[int(keys2['Lidnummer'][1]),keys2['Naam'][1],keys2['E-mail'][1]]
#  return lid

def read_member_csv(file):
  m = []
  for l in open(file).readlines()[1:]: # Skip first line
    if l: #Skip empty lines
      m.append(csvsplit(l))
  return m

def read_member_csv2(file):
  m = []
  for l in open(file).readlines()[1:]: # Skip first line
    if l: #Skip empty lines
      m.append(csvsplit2(l))
  return m

def sorteer(array,var,rev):
  return sorted(array, key=lambda kolom: kolom[var], reverse=bool(rev))

#Data structure
keys={'Lidnummer':[0,0],'E-mail':[6,''],'Straat':[7,''],'Postcode':[8,''],'Woonplaats':[9,''],'Achternaam':[1,''],'Tussenvoegsel':[3,''],'Voornaam':[2,'']}
keys2={'Lidnummer':[0,0],'E-mail':[7,''],'Straat':[8,''],'Postcode':[9,''],'Woonplaats':[10,''],'Achternaam':[1,''],'Tussenvoegsel':[3,''],'Voornaam':[2,'']}

infile=sys.argv[1]
infile2=sys.argv[2]

leden=read_member_csv(infile)
leden2=read_member_csv2(infile2)

postcodes={'Amsterdam':[[1000,2159],[8200,8259]],'LeidenHaaglanden':[[2160,2799]],'Rotterdam':[[2800,3399],[4300,4599]],'Utrecht':[[3400,4299],[6700,6799],[6860,6879],[7300,7399],[8260,8299]],'Brabant':[[4600,5339],[5460,5799]],'Nijmegen':[[5340,5459],[5800,5999],[6500,6699],[6800,6859],[6880,7099],[7200,7299]],'Maastricht':[[6000,6499]],'Twente':[[7100,7199],[7400,7699],[8100,8199]],'Groningen':[[7700,7999],[9300,9999]],'Friesland':[[8300,9299]],'Zwolle':[[8000,8099]]}

oldset=set(lid[0] for lid in leden2)
newset=set(lid[0] for lid in leden)

nieuweleden=newset-oldset
oudleden=oldset-newset
bestaandeleden=oldset & newset
amsterdam=leidenhaaglanden=rotterdam=utrecht=brabant=nijmegen=maastricht=twente=groningen=friesland=set()


for i in range(len(leden)):
  if leden[i][0] in bestaandeleden:
    if leden[i][0] != leden2[i][0]:
      print(leden[i][1])

#for i in range(len(leden)):
#  if leden[i][0] in nieuweleden:
#    print(leden[i][1],",",leden[i][2],",1,1",sep='')

#oudfile="oudlid.csv"
#for i in range(len(leden2)):
#  if leden2[i][0] in oudleden:
#    if leden2[i][2]!="": 
#      print(leden2[i][2])


#afdelingen=[[amsterdam,[[1000,2159],[8200,8259]]],[leidenhaaglanden,[[2160,2799]]],[rotterdam],[utrecht],[brabant],[nijmegen],[maastricht],[twente],[groningen],[friesland]]
#
#for i in sorted(leden, key=lambda kolom: kolom[0]):
#  k=0
#  for j in sorted(leden2, key=lambda kolom: kolom[0]):
#    if i[0]==j[0] and i[2]!=j[2]:
#      k=1
#      break
#    continue
#    #print i
#  if k==1:
#    print(i[1],",",i[2],",1,1",sep='')
##    print(j[1],",",j[2],",1,1",sep='')
#
#i=0
#for afdeling in afdelingen:
#  for j in range(len(afdelingen[i][1])):
#    #...
#  i+=1
  
#for afdeling in postcodes:
#  for i in range(len(postcodes[afdeling])):
##    print afdeling
##    print i
##    print postcodes[afdeling][i][0]
#    for lid in leden:
#      if (lid[5] != []):
#        if len(lid[5][0]) == 4:
#          if (int(lid[5][0])<=postcodes[afdeling][i][1] and int(lid[5][0])>=postcodes[afdeling][i][0]):
#            afdelinglid.append(afdeling)

#for lid in sorteer(leden,0,0):
#  try:
#    if lid[6]:
#      continue
#      #print lid[0],",",lid[1],",",lid[4],",",lid[6]
#  except:
#    print lid[0],",",lid[1],",",lid[2],",",lid[3],",",lid[4],",",lid[5]
#
