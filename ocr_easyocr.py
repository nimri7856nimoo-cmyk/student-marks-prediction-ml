import easyocr
import cv2
import re
import os

reader = easyocr.Reader(['en'], gpu=False)

def extract_info(results):
    texts = [res[1].strip() for res in results]
    full_text = ' '.join(texts)

    name = "Not Found"
    father = "Not Found"
    gender = "Not Found"
    country = "Not Found"
    cnic = "Not Found"
    dob = "Not Found"
    date_issue = "Not Found"
    date_expiry = "Not Found"

    for i, text in enumerate(texts):
        # Name
        if text.strip().lower() == 'name':
            if i + 1 < len(texts):
                val = texts[i + 1]
                if len(val) > 3 and not any(c.isdigit() for c in val):
                    name = val

        # Father Name
        if 'father' in text.lower():
            if i + 1 < len(texts):
                val = texts[i + 1]
                if len(val) > 3 and not any(c.isdigit() for c in val):
                    father = val

        # ✅ GENDER FIXED
        if 'gender' in text.lower():
            for j in range(i+1, min(i+5, len(texts))):
                val = texts[j].strip().upper()
                if val == 'M' or val == 'MALE':
                    gender = 'Male'
                    break
                elif val == 'F' or val == 'FEMALE':
                    gender = 'Female'
                    break

        # Country
        if re.search(r'country|stay', text, re.IGNORECASE):
            for j in range(i+1, min(i+3, len(texts))):
                val = texts[j]
                if 'pakistan' in val.lower():
                    country = 'Pakistan'
                    break
                elif len(val) > 2 and not any(c.isdigit() for c in val):
                    country = val
                    break

        # CNIC
        digits = re.sub(r'[^0-9]', '', text)
        if len(digits) >= 13 and cnic == "Not Found":
            raw = digits[:13]
            cnic = f"{raw[:5]}-{raw[5:12]}-{raw[12]}"

        # Dates
        dates = re.findall(r'\d{2}[./]\d{2}[./]\d{4}', text)
        for d in dates:
            d = d.replace('/', '.')
            try:
                parts = d.split('.')
                if len(parts) == 3:
                    day = int(parts[0])
                    month = int(parts[1])
                    year = int(parts[2])
                    # Fix swapped month/day
                    if month > 12:
                        parts[0], parts[1] = parts[1], parts[0]
                        d = '.'.join(parts)
                        year = int(parts[2])
                        month = int(parts[1])
                    if 1950 <= year <= 2010:
                        if dob == "Not Found":
                            dob = d
                    elif date_issue == "Not Found":
                        date_issue = d
                    elif date_expiry == "Not Found":
                        date_expiry = d
            except:
                pass

    # Fallbacks
    if country == "Not Found" and 'pakistan' in full_text.lower():
        country = 'Pakistan'

    if gender == "Not Found":
        for i, text in enumerate(texts):
            if text.strip().upper() == 'M':
                gender = 'Male'
                break
            elif text.strip().upper() == 'F':
                gender = 'Female'
                break

    return {
        "Name"          : name,
        "Father Name"   : father,
        "Gender"        : gender,
        "Country"       : country,
        "CNIC Number"   : cnic,
        "Date of Birth" : dob,
        "Date of Issue" : date_issue,
        "Date of Expiry": date_expiry
    }

# Process all images
folder = "id_cards_folder"
images = [f for f in os.listdir(folder)
          if f.startswith('id') and f.endswith(('.jpg', '.jpeg', '.png'))]

print(f"Total images found: {len(images)}")
print("=" * 50)

success = 0
failed = []
total_accuracy = 0

for img_name in sorted(images):
    path = os.path.join(folder, img_name)
    img = cv2.imread(path)

    if img is None:
        print(f"❌ Could not load: {img_name}")
        failed.append(img_name)
        continue

    # Preprocess
    img_resized = cv2.resize(img, None, fx=2, fy=2,
                             interpolation=cv2.INTER_CUBIC)

    results = reader.readtext(img_resized)
    info = extract_info(results)

    print(f"\n📄 Image: {img_name}")
    print("-" * 40)
    for key, val in info.items():
        status = "✅" if val != "Not Found" else "❌"
        print(f"{status} {key:15}: {val}")

    found = sum(1 for v in info.values() if v != "Not Found")
    total = len(info)
    accuracy = round((found/total)*100)
    total_accuracy += accuracy
    print(f"Accuracy: {found}/{total} fields ({accuracy}%)")

    if found >= 6:
        success += 1
    else:
        failed.append(img_name)

avg_accuracy = round(total_accuracy / len(images))

print("\n" + "=" * 50)
print(f"✅ Successfully processed : {success}/{len(images)}")
print(f"📊 Average Accuracy       : {avg_accuracy}%")
print(f"❌ Issues found in        : {len(failed)} images")
if failed:
    print(f"Problem images           : {failed}")
    