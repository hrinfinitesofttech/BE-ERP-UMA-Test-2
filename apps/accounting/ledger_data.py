"""Master data lifted from the client's Excel (UMA TECHNO FAB): groups, ledgers, depreciation chart, stock."""

# (name, parent, nature, sort)
GROUPS = [
    ('Capital Account', None, 'Capital', 10),
    ('Profit & Loss A/c', None, 'Capital', 15),
    ('Loans (Liability)', None, 'Loans', 20),
    ('Current Liabilities', None, 'CurrentLiabilities', 30),
    ('Duties & Taxes', 'Current Liabilities', 'CurrentLiabilities', 31),
    ('Sundry Creditors', 'Current Liabilities', 'CurrentLiabilities', 32),
    ('Fixed Assets', None, 'FixedAssets', 40),
    ('Investments', None, 'Investments', 50),
    ('Current Assets', None, 'CurrentAssets', 60),
    ('Stock-in-hand', 'Current Assets', 'CurrentAssets', 61),
    ('Loans & Advances (Asset)', 'Current Assets', 'CurrentAssets', 62),
    ('Sundry Debtors', 'Current Assets', 'CurrentAssets', 63),
    ('Cash-in-hand', 'Current Assets', 'CurrentAssets', 64),
    ('Bank Accounts', 'Current Assets', 'CurrentAssets', 65),
    ('Tax Receivables', 'Current Assets', 'CurrentAssets', 66),
    ('Sales Accounts', None, 'Sales', 70),
    ('Purchase Accounts', None, 'Purchase', 80),
    ('Direct Incomes', None, 'DirectIncome', 90),
    ('Indirect Incomes', None, 'IndirectIncome', 100),
    ('Direct Expenses', None, 'DirectExpense', 110),
    ('Indirect Expenses', None, 'IndirectExpense', 120),
]

# group -> (list of ledger names, opening_type)
LEDGERS = {
    'Capital Account': (['Kantibhai Manvar Capital A/C-50%', 'Pankaj Manvar-Capital A/C 50%'], 'Cr'),
    'Profit & Loss A/c': (['Profit & Loss A/c (Opening Balance)'], 'Cr'),
    'Loans (Liability)': (['Bank OD A/c.', 'Secured Loans', 'Unsecured Loans'], 'Cr'),
    'Current Liabilities': (['Suspance A/c'], 'Cr'),
    'Duties & Taxes': (['CGST Output', 'SGST Output', 'IGST Output', 'CGST Input', 'SGST Input', 'IGST Input',
                        'TDS Payable', 'GST Payable'], 'Cr'),
    'Fixed Assets': (['10 % BLOCK', '10 % BLOCK ELECTRICAL FITTING', '15% BLOCK', '40% BLOCK',
                      'Non Depreciable Assets'], 'Dr'),
    'Investments': (['SIDBI BANK FD FOR LOAN'], 'Dr'),
    'Stock-in-hand': (['Opening Stock'], 'Dr'),
    'Loans & Advances (Asset)': (['Loans & Advances (Asset)'], 'Dr'),
    'Cash-in-hand': (['Cash-in-hand'], 'Dr'),
    'Bank Accounts': (['Bank Account (Main)'], 'Dr'),
    'Tax Receivables': (['ADVANCE TAX', 'GST TDS Receivable', 'TCS', 'TDS Receivable'], 'Dr'),
    'Sales Accounts': (['SALES GST @ 18%', 'SALES INVOICE (OGS)', 'LABOUR SALE', 'Courier Charge',
                        'Freight for Sale', 'Rate Diff.', 'WEIGHT DIFFRENT'], 'Cr'),
    'Purchase Accounts': (['Purchase- GST Local', 'Purchase - GST (OGS)', 'Rate Difference'], 'Dr'),
    'Direct Incomes': (['DISCOUNT', 'Packing & Forwading Charge'], 'Cr'),
    'Indirect Incomes': (['Insurance', 'Other Service', 'Round Off', 'Solar Subsidiy'], 'Cr'),
    'Direct Expenses': (['SALARY EXPENSES', 'LABOUR CHARGES - TDS', 'Freight and Transportation Exps', 'CARTAGE',
                         'Courier Exps', 'BURNING EXP', 'CUTTING CHARGES', 'Electric Bill', 'HANDLING CHARGE',
                         'LOADING CHARGES', 'LOADING CHARGES GST', 'Loading Unloadnig Exp', 'Packing Charges',
                         'Other Expense'], 'Dr'),
    'Indirect Expenses': (['BANK INTEREST', 'BANK LOAN CHARGES', 'INSURANCE EXPS', 'CANTEEN EXPS', 'Consulting Charge',
                           'DHARMADA EXPS', 'Kasar', 'Legal Fee', 'Marketing Exp.', 'Mics. Exp.', 'OFFICE EXPENSES',
                           'Petrol Allowance', 'PETROL & DIESEL EXPENSES', 'Professional Fee',
                           'RAJPUR GRAM PANCHAYAT', 'REPAIR AND MAINTANCE', 'Reparing and Services',
                           'Sabarmati Gas Limited', 'Sales on Commission', 'STAFF WELFARE EXP',
                           'Stamping Service Charges', 'Stationery Exp.', 'Tds Interest', 'Vehical Exp.',
                           'DEPRECIATION'], 'Dr'),
}

# (group_name, particulars, rate)  -- 36 assets, same order as the Excel
DEPRECIATION_ASSETS = [
    ('Non Depreciable Assets', 'NON DEPRCIABEL ASSETS MOBILE', 0),
    ('Non Depreciable Assets', 'SURVEY NO 1040/4', 0),
    ('10% BLOCK ELECTRICAL FITTING', 'DELL LED', 10),
    ('10% BLOCK ELECTRICAL FITTING', 'DRAYER FAN', 10),
    ('10% BLOCK ELECTRICAL FITTING', 'ELECTRICAL WIRING & FITTING EXPENSE', 10),
    ('10% BLOCK ELECTRICAL FITTING', 'Electric Fitting', 10),
    ('10% BLOCK', 'Factory Construction', 10),
    ('10% BLOCK', 'Furniture & Fixtures', 10),
    ('15% BLOCK', '5 HP AIR COMPRESOR', 15),
    ('15% BLOCK', '7.5 HP IC TUBE COMPAITE', 15),
    ('15% BLOCK', 'AIRCONDITIONER', 15),
    ('15% BLOCK', 'AIR VENTILATOR', 15),
    ('15% BLOCK', 'Bio-Matric Mashine', 15),
    ('15% BLOCK', 'BOLERO PIK -UP FB PS 1.7T XL BS6', 15),
    ('15% BLOCK', 'CAMERA', 15),
    ('15% BLOCK', 'CCTV CAMERA', 15),
    ('15% BLOCK', 'CIAZ ALFA', 15),
    ('15% BLOCK', 'CNC HYDROLIC PRESS MACHINE', 15),
    ('15% BLOCK', 'CNC LASER CUTTING MACHINE (BRAHMASTRA PRIME)', 15),
    ('15% BLOCK', 'CRETA WHITE', 15),
    ('15% BLOCK', 'DIGITAL ULTRASONIC MACHINE', 15),
    ('15% BLOCK', 'FOOD MACHINE', 15),
    ('15% BLOCK', 'HANDHELD LASER WELDING MACHINE', 15),
    ('15% BLOCK', 'INCLINE Z TYPR MODULAR CONVEYOR', 15),
    ('15% BLOCK', 'LED TV', 15),
    ('15% BLOCK', 'Machinery', 15),
    ('15% BLOCK', 'Mobile', 15),
    ('15% BLOCK', 'PRINTER', 15),
    ('15% BLOCK', 'Refrigerator', 15),
    ('15% BLOCK', 'ROTI MAKING MACHINE', 15),
    ('15% BLOCK', 'Solar Power Genretive System', 15),
    ('15% BLOCK', 'Water Cooler', 15),
    ('40% BLOCK', 'ANTIVIRUS PURCHASE', 40),
    ('40% BLOCK', 'COMPUTER', 40),
    ('40% BLOCK', 'LAPTOP', 40),
    ('40% BLOCK', 'SOFTWARE DESIGN', 40),
]

# Depreciation block name -> Fixed Assets ledger name
BLOCK_LEDGER = {
    'Non Depreciable Assets': 'Non Depreciable Assets',
    '10% BLOCK ELECTRICAL FITTING': '10 % BLOCK ELECTRICAL FITTING',
    '10% BLOCK': '10 % BLOCK',
    '15% BLOCK': '15% BLOCK',
    '40% BLOCK': '40% BLOCK',
}

FINISHED_GOODS = [
    'Filter (Fryer Line)', 'Flavor Applicator', 'Fryer', 'HOT AIR GENERATOR', 'Laser Cutting (M.S. Plate)',
    'Laser Cutting (S.S.Plate)', 'Machinery Part', 'MACHINERY SPARTS', 'Machine Sparts', 'M.S. DUCT LINE',
    'M.S. Dust Collector', 'M.S. PLATE LASER CUTTING', 'Namkeen Mixture', 'Plant Machinery Fitting and Installation',
    'Pre Fryer Rotary Drum', 'SS 304 Cooling Jacket', 'S.S. 310 Muffle', 'SS Conveyor', 'S.S. Reactor',
    'S.S. Shell Bending',
]

RAW_MATERIAL = {
    'Steel & M.S. Material': [
        'M S PLATE', 'MS SHEET', 'M S PIPE', 'MS Round Bar', 'MS ANGLE CHANNEL PATTI PATTA', 'MS Flange',
        'M.S. NUT / BOLT', 'SCRAP', 'Rcc Half Round Pipe'],
    'Stainless Steel (SS 304 / 316)': [
        'SS PLATE', 'SS SHEET', 'S S PIPE', 'S S PIPE SEAMLESS', 'S S COIL', 'SS Round Bar',
        'SS ANGLE CHANNEL PATTI PATAA', 'SS FITTINGS', 'SS Bend', 'SS Flexible Corrugated Hose Pipe',
        'S S Bright Wire', 'SS BOLT', 'M12 SS 304 NYLOCK NUT', 'S.S. 304 GRUB SCREW'],
    'Hardware, Fasteners & Welding': [
        'ALLEN CAP', 'CSK SCREW', 'DOME NUT', 'HEX BOLT', 'HEX NUT', 'TIG WIRE', 'TUNGSTEN ROAD', 'WELDING ROD',
        'FILLER WIER', 'CUTTING DISC 12"', 'Consumable', 'Grease', 'HARDWARE', 'Packing Sheet', 'PLUG', 'WHEEL'],
    'Electrical, Control Panels & Motors': [
        'Control Panel', 'Extruder Control Panel', 'Double Extruder Control Panel', 'Single Extruder Control Panel',
        'PANEL BOARD', 'Panel Boards', 'Controller', 'Linear Feeder with Controller', 'MOTOR', 'PUMP',
        'Pump Sparts', 'Blower Id Fan', 'Air Blower'],
    'Parts, Gear & Instruments': [
        'BEARING', 'BELLO', 'BEND', 'LONG BEND', 'Burner', 'C.I. Casting', 'CONVEYOR BELT', 'COUPLING', 'GEAR',
        'Gear Flange', 'HOSE PIPE', 'NIPLE', 'NOZZLE', 'PRESSURE GAUGES', 'LEVEL INDICATOR (S.S.304)',
        'LEVEL INDICATOR (S.S.316)', 'PTFE SHEET & BUSH', 'REDUCER', 'SN 2235', 'VALVE', 'MECHANICAL SEAL',
        '1.8mm x 1220 Fiber Sheet', '8.5" - 9.5" Namkeen Disc', 'Alluminium Parts', 'ALLUMINIUM ROUND BAR',
        'Aluminum Pulley', 'BLIND FLANGE', 'Extruder Gunmetal Warm', 'GUN METAL CASTING',
        'Insize Micro Meter 100-200', 'Screwberal 41B', 'SHAFT MATEL', 'Z Inline Convetor System'],
}
