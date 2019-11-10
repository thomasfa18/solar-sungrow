#Valid for device types:
#SG30KTL-M,SG30KTL-M-V31,SG33KTL-M,SG36KTL-M,SG33K3J,SG49K5J,SG34KJ,LP_P34KSG,SG50KTL-M-20,SG60KTL,SG80KTL,SG80KTL-20,SG60KU-M,SG5KTL-MT,SG6KTL-MT,SG8KTL-M,
#SG10KTL-M,SG10KTL-MT,SG12KTL-M,SG15KTL-M,SG17KTL-M,SG20KTL-M,SG80KTL-M,SG111HV,SG125HV,SG125HV-20,SG33CX ,SG40CX,SG50CX,SG110CX,SG30KTL,SG10KTL,SG12KTL,
#SG15KTL,SG20KTL,SG30KU,SG36KTL,SG36KU,SG40KTL,SG40KTL-M,SG50KTL-M,SG60KTL-M,SG60KU
#Statement:
#All hardware versions of SG60KTL share one device type code

#Data type
#U16: 16-bit unsigned integer, big-endian
#S16: 16-bit signed integer, big-endian
#U32: 32-bit unsigned integer; little-endian for double-word data. Big-endian for byte data
#S32: 32-bit signed integer; little-endian for double-word data. Big-endian for byte data

# [description, register, type, format]
#Address of 3x type is read-only register, supporting the cmdcode inquiry of 0x04.

sungrow_registers = [
  #['4990 ~ 4999 - Serial number',4990,'STR16','ENUM'],
  #['5001 - Nominal Output power',5001,'U16','FIX1'], #0.1kWh, inverter rating
  #['5003 - Daily power yields',5003,'U16','FIX1'], #0.1kWh
  #['5004 - Total power yields',5004,'U32','FIX0'], #kWh
  #['5006 - Total running time',5006,'U32','Duration'], #hours
  ['5008 - Internal temperature',5008,'S16','FIX1'], #C
  #['5009 - Total apparent power',5009,'U32','FIX0'], #VA
  ['5011 - MPPT 1 voltage',5011,'U16','FIX1'], #0.1V
  ['5012 - MPPT 1 current',5012,'U16','FIX1'], #0.1A
  ['5013 - MPPT 2 voltage',5013,'U16','FIX1'], #0.1V
  ['5014 - MPPT 2 current',5014,'U16','FIX1'], #0.1A
  #['5015 - MPPT 3 voltage',5015,'U16','FIX1'], #0.1V
  #['5016 - MPPT 3 current',5016,'U16','FIX1'], #0.1A
  ['5017 - Total DC power',5017,'U32','FIX0'], #Watts, cumulative power across all MPPTs
  ['5019 - Phase A voltage',5019,'U16','FIX1'], #0.1V
  #['5020 - Phase B voltage',5020,'U16','FIX1'], #0.1V
  #['5021 - Phase C voltage',5021,'U16','FIX1'], #0.1V
  ['5022 - Phase A current',5022,'U16','FIX1'], #0.1A
  #['5023 - Phase B current',5023,'U16','FIX1'], #0.1A
  #['5024 - Phase C current',5024,'U16','FIX1'], #0.1A
  ['5031 - Total active power',5031,'U32','FIX0'], #Watts
  #['5033 - Total reactive power',5033,'S32','FIX0'], #variance
  ['5035 - Power factor',5035,'S16','FIX1000'], #0.001
  #['5036 - Grid frequency',5036,'U16','FIX1'], #0.1Hz
  #['5049 - Nominal reactive power',5049,'U16','FIX1'], #kilovariance
  #['5083 - Meter power',5083,'S32','FIX'], #W
  #['5085 - Meter A phase power',5085,'S32','FIX'], #W
  #['5087 - Meter B phase power',5087,'S32','FIX'], #W
  #['5089 - Meter C phase power',5089,'S32','FIX'], #W
  #['5097 - Daily import energy',5097,'U32','FIX1'], #0.1kWh
  #['5113 - Daily running time',5113,'U16','Duration'], #minutes
  #['5144 - Total power yields',5144,'U32','FIX1'], #0.1kWh
  #['5146 - Negative voltage to ground',5146,'S16','FIX1'], #0.1V
  ['5148 - Grid frequency',5148,'U16','FIX2'] #0.01Hz
  ]

scan = "{}"