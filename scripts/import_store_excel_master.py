import os
import sys
import re
import sqlite3
import openpyxl

DB_PATH = r'd:\UMA ERP Test 3\BE-ERP-UMA-Test-2\db.sqlite3'
FILE_PATH = r'C:\Users\91760\.gemini\antigravity\brain\65e8786a-3c94-4f7f-80a8-a3fb048c518d\.user_uploaded\media_1795090789683_d436302b.xlsx'

UOM_DEFINITIONS = [
    ('NOS', 'Numbers / Pieces', 'Individual discrete units or pieces'),
    ('KG', 'Kilograms', 'Weight in kilograms'),
    ('KGS', 'Kilograms (Kgs)', 'Weight in kilograms'),
    ('MTR', 'Meters', 'Length in meters'),
    ('ROLL', 'Rolls', 'Roll of material or tape'),
    ('SET', 'Sets', 'Paired set of parts'),
    ('LTR', 'Liters', 'Volume in liters'),
    ('BOX', 'Boxes', 'Box package'),
    ('PKT', 'Packets', 'Packet bundle'),
    ('BAG', 'Bags / Katta', 'Bag of material'),
    ('PAIR', 'Pairs', 'Pair of items'),
    ('SQM', 'Square Meters', 'Area in square meters'),
]

CATEGORY_MAP = {
    'ALLEN CAP': ('FAST-ALN', 'Allen Cap Screws', 'High tensile hex socket allen cap screws'),
    'BEAM': ('MET-BEAM', 'Structural Beams', 'ISMB and MS structural beams'),
    'BEARING': ('MOT-BRG', 'Bearings & Housings', 'Ball bearings, roller bearings, and UCF/UCP pedestal housings'),
    'BELLO': ('FIT-BEL', 'Bellows & Expansion Joints', 'Axial and circular expansion bellows'),
    'C.I.CASTING': ('CAST-CI', 'C.I. Castings', 'Cast iron machine bodies and custom castings'),
    'CONVEYOR BELT': ('MOT-CBLT', 'Conveyor Belts & Mesh', 'PU, SS, and wire mesh conveyor belts'),
    'CR SHEET': ('MET-CRS', 'CR Sheets', 'Cold rolled steel sheets'),
    'CSK SCREW': ('FAST-CSK', 'CSK Screws', 'Countersunk allen and self-drilling screws'),
    'FILLER WIRE': ('WELD-WIRE', 'Filler Wire & TIG', 'SS 308/316 and MS filler welding wire'),
    'GAS CYLINDER': ('GAS-CYL', 'Industrial Gas Cylinders', 'Oxygen, Nitrogen, Argon, and LPG commercial cylinders'),
    'GEAR BOX': ('MOT-GBX', 'Gear Boxes & Reducers', 'Worm reduction and inline helical gearboxes (Bonfiglioli/Roboox)'),
    'GEAR FLANGE': ('MOT-GFLG', 'Gearbox Flanges', 'Output and motor mounting flanges for gearboxes'),
    'GEAR PUMP': ('MOT-PMP', 'Gear Pumps & Pumpsets', 'Rotary gear pumps, submersible pumps, and centrifugal pumps'),
    'HARDWARE': ('GEN-HRD', 'General Hardware & Fasteners', 'General workshop fasteners, brackets, and accessories'),
    'ELECTRICAL': ('ELEC-PARTS', 'Electrical Components & Wiring', 'Cables, contactors, VFDs, switches, MCBs, and panels'),
    'GRINDING & BUFFING DISC': ('TOOL-DISC', 'Abrasive Discs & Wheels', 'Cutting wheels, grinding discs, flap wheels, and buffing discs'),
    'LASER PART': ('MACH-LASER', 'Laser Machine Consumables', 'Laser cutting nozzles, protective windows, lenses, and shield caps'),
    'LUBRICANT': ('CHEM-LUB', 'Oils & Lubricants', 'Machine oil, cutting fluid, gear oil, grease, and cleaners'),
    'OIL & PAINS': ('CHEM-PNT', 'Paints & Primers', 'Industrial enamel paints, primers, thinners, and spray cans'),
    'OIL SEAL': ('SEAL-OIL', 'Oil Seals & O-Rings', 'NBR oil seals, rubber O-rings, and mechanical seals'),
    'PLASMA PARTS': ('MACH-PLAS', 'Plasma Machine Consumables', 'Plasma torches, electrodes, nozzles, swirl rings, and retaining caps'),
    'PVC FITTINGS': ('FIT-PVC', 'PVC & UPVC Fittings', 'UPVC pipes, ball valves, tees, elbows, and solvent cements'),
    'TOOLS': ('TOOL-MCH', 'Machine Tools & Cutters', 'HSS drill bits, end mills, lathe turning tools, and tool holders'),
    'V-BELT': ('MOT-VBLT', 'Transmission V-Belts', 'Classical and wedge transmission V-belts'),
    'WELDING MATERIAL': ('WELD-ACC', 'Welding Safety & Accessories', 'Welding helmets, goggles, glass, cables, and torches'),
    'HEX BOLT': ('FAST-HEXB-304', 'SS 304 Hex Bolts', 'Stainless steel grade 304 hex head bolts'),
    'SS-316 HEX BOLT': ('FAST-HEXB-316', 'SS 316 Hex Bolts', 'Stainless steel grade 316 hex head bolts'),
    'HEX NUT': ('FAST-NUT-NYL', 'Nylock Nuts', 'Nylon insert lock nuts'),
    'SS-304 HEX NUT': ('FAST-NUT-304', 'SS 304 Hex Nuts', 'Stainless steel grade 304 hex nuts'),
    'SS-316 HEX NUT': ('FAST-NUT-316', 'SS 316 Hex Nuts', 'Stainless steel grade 316 hex nuts'),
    'MOTOR': ('MOT-ELEC', 'Electric Motors', 'AC induction motors (flange/foot mount IE2/IE3)'),
    'MS ANGLE CHANNEL PATTI PATTA': ('MET-MS-SEC', 'MS Angles, Channels & Flats', 'Mild steel structural angles, channels, and flat bars'),
    'MS BEND': ('FIT-MS-BND', 'MS Bends & Elbows', 'Mild steel seamless and welded pipe bends'),
    'MS COUPLLING': ('FIT-MS-CPL', 'MS Couplings', 'Mild steel threaded and socket weld couplings'),
    'MS FLANGE': ('FIT-MS-FLG', 'MS Flanges', 'Mild steel slip-on and blind flanges'),
    'MS NUT - BOLT': ('FAST-MS-BLT', 'MS Hex Bolts & Nuts', 'Mild steel and high tensile hex bolts and nuts'),
    'MS PIPE': ('MET-MS-PIPE', 'MS Pipes & Tubes', 'Mild steel ERW, seamless, and square hollow section pipes'),
    'MS PLATE': ('MET-MS-PLT', 'MS Plates', 'Mild steel hot rolled and plasma cut plates'),
    'MS ROUND BAR': ('MET-MS-ROD', 'MS Round Bars', 'Mild steel and bright drawn solid round bars'),
    'MS SHEET': ('MET-MS-SHT', 'MS Sheets', 'Mild steel cold rolled and hot rolled sheets'),
    'NIPPLE': ('FIT-NPP', 'Pipe Nipples', 'Threaded pipe barrel and hex nipples'),
    'SS NIPPLE': ('FIT-SS-NPP', 'SS Pipe Nipples', 'Stainless steel threaded hex and barrel nipples'),
    'NOZEL': ('TOOL-NOZ', 'Caliber Nozzles', 'Single and double caliber cutting nozzles'),
    'PACKING MATERIALS': ('GEN-PACK', 'Packaging Materials', 'Stretch film, strapping, and PTFE ring gaskets'),
    'PANNEL BOARD': ('ELEC-PNL', 'Electrical Control Panels', 'VFD control panels, extruder automation panels, and starter boxes'),
    'PLUG': ('FIT-PLG', 'Pipe Plugs', 'Threaded hex and square head pipe plugs'),
    'PTFE SHEET & BUSH': ('SEAL-PTFE', 'PTFE Bush & Sheets', 'Teflon sheets, bushes, and silicone rubber seals'),
    'PUMP': ('MOT-WPMP', 'Industrial Pumps', 'Chemical gear pumps, circulation pumps, and water pumps'),
    'REDUCER': ('FIT-RED', 'Pipe Reducers', 'Concentric and eccentric pipe reducers'),
    'SS-304 GURB SCREW': ('FAST-GRB-304', 'SS 304 Grub Screws', 'Stainless steel socket head set/grub screws'),
    'SS-304 LIMIPET COIL': ('MET-SS-LMPT', 'SS Limpet Coils', 'Stainless steel reactor jacket limpet half-pipe coils'),
    'SS ANGLE/PATTI/PATA': ('MET-SS-SEC', 'SS Angles & Flats', 'Stainless steel structural angles and flat bars'),
    'SS BEND': ('FIT-SS-BND', 'SS Pipe Bends', 'Stainless steel schedule 10/40 pipe bends'),
    'SS LONG BEND': ('FIT-SS-LBND', 'SS Long Bends', 'Stainless steel long radius pipe bends'),
    'SS SHORT BEND': ('FIT-SS-SBND', 'SS Short Bends', 'Stainless steel short radius pipe bends'),
    'SS COIL': ('MET-SS-COIL', 'SS Coils', 'Stainless steel hot/cold rolled coils'),
    'SS COUPLLING': ('FIT-SS-CPL', 'SS Couplings', 'Stainless steel half and full threaded couplings'),
    'SS DOME NUT': ('FAST-DMN-SS', 'SS Dome Nuts', 'Stainless steel decorative and cap dome nuts'),
    'SS-304 FLANGE': ('FIT-FLG-304', 'SS 304 Flanges', 'Stainless steel grade 304 SORF, slip-on and blind flanges'),
    'SS - 316 FLANGE': ('FIT-FLG-316', 'SS 316 Flanges', 'Stainless steel grade 316 ASA 150# flanges'),
    'SS CAP': ('FIT-SS-CAP', 'SS Pipe Caps', 'Stainless steel schedule 10 dish and end caps'),
    'SS ELBOW': ('FIT-SS-ELB', 'SS Pipe Elbows', 'Stainless steel 45 and 90 degree pipe elbows'),
    'SS FLATE BAR': ('MET-SS-FLT', 'SS Flat Bars', 'Stainless steel flat and square bars'),
    'SS FLEXIBLE PIPE': ('FIT-SS-HSE', 'Flexible Hose & Corrugated Pipes', 'SS flexible corrugated hoses and industrial rubber hoses'),
    'SS CORUGT PIPE': ('FIT-SS-CORR', 'SS Corrugated Pipes', 'Stainless steel flexible corrugated connection pipes'),
    'SS PIPE': ('MET-SS-PIPE', 'SS Pipes (Welded/ERW)', 'Stainless steel schedule 10 and square hollow section pipes'),
    'SS - 304 PIPE': ('MET-SS304-PIPE', 'SS 304 Pipes', 'Stainless steel grade 304 seamless and welded pipes'),
    'SS - 316 PIPE': ('MET-SS316-PIPE', 'SS 316 Pipes', 'Stainless steel grade 316 schedule 10/40 pipes'),
    'SS PIPE SEAMLESS': ('MET-SS-SMLS', 'SS Seamless Pipes', 'Stainless steel high pressure seamless tubes and pipes'),
    'SS PLATE': ('MET-SS-PLT', 'SS Plates', 'Stainless steel industrial plates and circles'),
    'SS - 304 PLATE': ('MET-SS304-PLT', 'SS 304 Plates', 'Stainless steel grade 304 plates and plasma cut blanks'),
    'SS - 310 PLATE': ('MET-SS310-PLT', 'SS 310 Plates', 'Heat resistant stainless steel grade 310 plates'),
    'SS - 316 PLATE': ('MET-SS316-PLT', 'SS 316 Plates', 'Corrosion resistant stainless steel grade 316 plates'),
    'SS ROUND BAR': ('MET-SS-ROD', 'SS Round Bars', 'Stainless steel solid round and bright bars'),
    'SS SHEEET': ('MET-SS-SHT', 'SS Sheets & Perforated', 'Stainless steel sheets and perforated filter sheets'),
    'STATONERY': ('GEN-STAT', 'Stationery & Office Supplies', 'Printing paper, files, markers, pens, and office stationery'),
    'TIG WIRE': ('WELD-TIG', 'TIG Welding Wire', 'TIG welding consumable rods'),
    'TUNGSTEN ROD': ('WELD-TUNG', 'Tungsten Electrodes', 'Tungsten TIG welding electrode rods'),
    'VALVE': ('FIT-VLV', 'Industrial Valves', 'Ball valves, gate valves, solenoid valves, and control valves'),
    'WASHER': ('FAST-WSH', 'Plain & Spring Washers', 'SS and MS flat plain and spring lock washers'),
    'WELDING ROD': ('WELD-ROD', 'Shielded Arc Welding Rods', 'MS and SS 308/316 flux coated arc welding electrodes'),
}

def guess_uom_for_item(item_name, category_name):
    name_l = item_name.lower()
    cat_l = category_name.lower()

    if any(x in name_l for x in ['plate', 'sheet', 'bar', 'channel', 'beam', 'angle', 'patta', 'flats', 'coil']) and not any(x in name_l for x in ['screw', 'bolt', 'nut']):
        return 'KG'
    if any(x in name_l for x in ['cable', 'wire', 'pipe', 'conveyor belt', 'rope', 'tape roll']):
        return 'MTR'
    if any(x in name_l for x in ['oil', 'chemical', 'paint', 'thinner', 'primer', 'cleaner']):
        return 'LTR'
    if any(x in name_l for x in ['set', 'tapset', 'pana set', 'gasket set']):
        return 'SET'
    if any(x in name_l for x in ['roll', 'film']):
        return 'ROLL'
    if any(x in name_l for x in ['box', 'packet', 'pkt']):
        return 'BOX'
    if any(x in name_l for x in ['gloves', 'gloze']):
        return 'PAIR'
    if any(x in name_l for x in ['cement', 'chokha', 'juvar', 'katta']):
        return 'BAG'
    return 'NOS'

def clean_item_code(raw_code, index):
    # Remove _x000D_
    c = re.sub(r'_x000D_', '', raw_code).strip()
    c = re.sub(r'[\r\n\t]+', ' ', c).strip()
    
    # Check if there is an existing code prefix like ALN 02- M10 x 20 -> ALN-02-M10X20
    m = re.match(r'^([A-Z0-9\s\-]+?)\s*[-:]\s*(.+)$', c)
    if m:
        prefix = re.sub(r'[^A-Z0-9]', '', m.group(1).upper())
        desc = re.sub(r'[^A-Z0-9]', '', m.group(2).upper())
        if len(prefix) >= 2 and len(prefix) <= 8:
            code = f"{prefix}-{desc[:12]}"
            return code[:24], c

    # Fallback to sanitized slug + index
    cleaned_name = re.sub(r'[^A-Z0-9]', '', c.upper())
    code = f"ITM-{cleaned_name[:12]}-{index:04d}"
    return code[:24], c

def run_import():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("Step 1: Seeding UOM Master...")
    for code, name, desc in UOM_DEFINITIONS:
        uom_id = f"UOM-{code}"
        cur.execute("""
            INSERT INTO store_uommaster (id, code, name, description)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET name=excluded.name, description=excluded.description
        """, (uom_id, code, name, desc))
    print(f"  -> {len(UOM_DEFINITIONS)} UOMs seeded.")

    print("\nStep 2: Seeding Item Categories...")
    seeded_categories = {}
    for raw_cat, (cat_code, cat_name, cat_desc) in CATEGORY_MAP.items():
        cat_id = f"CAT-{cat_code}"
        cur.execute("""
            INSERT INTO store_itemcategory (id, code, name, description)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET name=excluded.name, description=excluded.description
        """, (cat_id, cat_code, cat_name, cat_desc))
        seeded_categories[raw_cat.upper()] = (cat_code, cat_name)
    print(f"  -> {len(CATEGORY_MAP)} Categories seeded.")

    print("\nStep 3: Loading Workbook 2 (Master Stock Register)...")
    wb = openpyxl.load_workbook(FILE_PATH, data_only=True)
    ws = wb['Raw Material']

    current_cat_raw = 'GENERAL'
    items_imported = 0
    used_codes = set()

    for r in range(3, ws.max_row + 1):
        c1 = str(ws.cell(r, 1).value or '').strip()
        c2 = str(ws.cell(r, 2).value or '').strip()
        c3 = str(ws.cell(r, 3).value or '').strip()

        if c1:
            clean_c1 = re.sub(r'[\r\n\t]+', ' ', c1).strip().upper()
            if clean_c1 in seeded_categories:
                current_cat_raw = clean_c1
            else:
                for k in seeded_categories:
                    if k in clean_c1 or clean_c1 in k:
                        current_cat_raw = k
                        break

        if c2 and c2.lower() not in ['particulars', 'quantity', 'total', 'nan']:
            clean_name = re.sub(r'_x000D_', '', c2).strip()
            clean_name = re.sub(r'[\r\n\t]+', ' ', clean_name).strip()
            if not clean_name:
                continue

            cat_info = seeded_categories.get(current_cat_raw)
            cat_code = cat_info[0] if cat_info else 'GEN'
            cat_name = cat_info[1] if cat_info else 'General Materials'

            # Parse opening quantity
            qty = 0.0
            if c3 and c3 != 'nan':
                try:
                    qty = float(c3.replace(',', '').strip())
                except ValueError:
                    qty = 0.0

            uom = guess_uom_for_item(clean_name, cat_name)
            base_code, clean_display_name = clean_item_code(clean_name, items_imported + 1)
            
            # Ensure unique item_code
            item_code = base_code
            counter = 1
            while item_code in used_codes:
                item_code = f"{base_code[:18]}-{counter}"
                counter += 1
            used_codes.add(item_code)

            item_id = f"ITM-{item_code}"

            # Insert/Update ItemMaster
            cur.execute("""
                INSERT INTO store_itemmaster (
                    id, item_code, item_name, item_type, category,
                    sub_category, description, specification, drawing_number,
                    brand_make, hsn_sac, gst_rate, uom, minimum_stock,
                    maximum_stock, reorder_level, unit_cost, status,
                    created_at, updated_at
                ) VALUES (
                    ?, ?, ?, 'Raw Material', ?,
                    '', ?, '', '',
                    '', '72193200', 18.0, ?, 10.0,
                    1000.0, 20.0, 0.0, 'Active',
                    datetime('now'), datetime('now')
                )
                ON CONFLICT(item_code) DO UPDATE SET
                    item_name=excluded.item_name,
                    category=excluded.category,
                    uom=excluded.uom,
                    updated_at=datetime('now')
            """, (
                item_id, item_code, clean_display_name, cat_name,
                f"Standard {cat_name} for engineering fabrication",
                uom
            ))

            # Insert/Update StockBalance
            stock_id = f"STK-{item_code}"
            cur.execute("""
                INSERT INTO store_stockbalance (
                    id, item_id, item_code, item_name, category, uom,
                    warehouse_id, warehouse_name, location, batch_lot,
                    quantity, reserved_quantity, available_quantity,
                    unit_rate, total_value, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?,
                    'wh-main', 'Main Raw Material Warehouse', 'Store Rack A', 'OPENING-STOCK',
                    ?, 0.0, ?,
                    0.0, 0.0, datetime('now')
                )
                ON CONFLICT(id) DO UPDATE SET
                    item_name=excluded.item_name,
                    category=excluded.category,
                    uom=excluded.uom,
                    quantity=excluded.quantity,
                    available_quantity=excluded.available_quantity,
                    updated_at=datetime('now')
            """, (
                stock_id, item_id, item_code, clean_display_name, cat_name, uom,
                qty, qty
            ))

            items_imported += 1

    conn.commit()
    conn.close()

    print(f"\n==========================================")
    print(f"IMPORT COMPLETE!")
    print(f"Total Items Imported: {items_imported}")
    print(f"==========================================")

if __name__ == '__main__':
    run_import()
