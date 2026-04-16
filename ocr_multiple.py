import pytesseract
import cv2
import re
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def preprocess(img):
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return gray

def try_rotations(img):
    rotations = [
        img,
        cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE),
        cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE),
        cv2.rotate(img, cv2.ROTATE_180)
    ]
    best_text = ""
    best_score = 0
    for rot in rotations:
        processed = preprocess(rot)
        text = pytesseract.image_to_string(processed, config=r'--oem 3 --psm 6')
        score = sum(1 for w in ['Pakistan', 'Name', 'Identity', 'Father', 'Gender', 'PAKISTAN']
                   if w.lower() in text.lower())
        if score > best_score:
            best_score = score
            best_text = text
    return best_text

def extract_info(text):
    lines = text.split('\n')
    lines = [l.strip() for l in lines if l.strip()]

    def clean_name(line):
        words = re.findall(r'\b[A-Z][a-z]{2,}\b', line)
        skip = {'Name', 'Father', 'Gender', 'Country', 'Date', 'Issue', 'Expiry',
                'Pakistan', 'Islamic', 'Republic', 'Identity', 'National', 'Card',
                'Under', 'Until', 'Birth', 'Stay', 'Holder', 'Signature',
                'Front', 'Back', 'Last', 'Mae', 'Translation'}
        words = [w for w in words if w not in skip]
        return ' '.join(words) if words else None

    name = "Not Found"
    father = "Not Found"
    cnic = "Not Found"
    dob = "Not Found"
    date_issue = "Not Found"
    date_expiry = "Not Found"

    for i, line in enumerate(lines):
        # Name — next line ke baad
        if re.fullmatch(r'Name', line.strip(), re.IGNORECASE):
            if i + 1 < len(lines):
                result = clean_name(lines[i + 1])
                if result:
                    name = result

        # Name same line mein
        if 'name' in line.lower() and 'father' not in line.lower() and name == "Not Found":
            result = clean_name(line)
            if result:
                name = result

        # Father Name — next line
        if re.search(r'father\s*name', line, re.IGNORECASE):
            if i + 1 < len(lines):
                result = clean_name(lines[i + 1])
                if result:
                    father = result

        # Father Name same line
        if 'father' in line.lower() and father == "Not Found":
            result = clean_name(line)
            if result:
                father = result

        # CNIC
        if any(c.isdigit() for c in line) and cnic == "Not Found":
            digits = re.sub(r'[^0-9]', '', line)
            if len(digits) >= 13:
                raw = digits[:13]
                cnic = f"{raw[:5]}-{raw[5:12]}-{raw[12]}"

        # Dates
        dates = re.findall(r'\d{2}\.\d{2}\.\d{4}', line)
        for d in dates:
            try:
                year = int(d.split('.')[-1])
                if 1950 <= year <= 2010:
                    dob = d
                elif date_issue == "Not Found":
                    date_issue = d
                elif date_expiry == "Not Found":
                    date_expiry = d
            except:
                pass

    return {
        "Name"          : name,
        "Father Name"   : father,
        "CNIC"          : cnic,
        "Date of Birth" : dob,
        "Date of Issue" : date_issue,
        "Date of Expiry": date_expiry
    }

# Process all images
folder = "."
images = [f for f in os.listdir(folder)
          if f.startswith('id') and f.endswith(('.jpg', '.jpeg', '.png'))]

print(f"Total images found: {len(images)}")
print("=" * 50)

success = 0
failed = []

for img_name in sorted(images):
    path = os.path.join(folder, img_name)
    img = cv2.imread(path)

    if img is None:
        print(f"❌ Could not load: {img_name}")
        failed.append(img_name)
        continue

    text = try_rotations(img)
    info = extract_info(text)

    print(f"\n📄 Image: {img_name}")
    print("-" * 40)
    for key, val in info.items():
        status = "✅" if val != "Not Found" else "❌"
        print(f"{status} {key:15}: {val}")

    found = sum(1 for v in info.values() if v != "Not Found")
    total = len(info)
    print(f"Accuracy: {found}/{total} fields detected")

    if found >= 4:
        success += 1
    else:
        failed.append(img_name)

print("\n" + "=" * 50)
print(f"✅ Successfully processed: {success}/{len(images)}")
print(f"❌ Issues found in      : {len(failed)} images")
if failed:
    print(f"Problem images         : {failed}")