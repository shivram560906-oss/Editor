# -*- coding: utf-8 -*-
"""
backend/calculator/remedies.py

Classical Parashari Vedic Astrology Remedies Engine.
Computes:
  1. Gemstone Recommendations (Life Stone, Lucky Stone, Punya/Knowledge Stone, Yogakaraka Stone)
     with metal, finger, auspicious day/time, weight, and wearing procedure.
  2. Forbidden / Caution Gemstones (Strict prohibitions for 6th, 8th, 12th lords and hostile combinations).
  3. Rudraksha Recommendations (1 to 14 Mukhi based on Lagna, Moon Nakshatra, Dasha lord, and afflicted planets).
  4. Vedic & Tantrik Mantras, Gayatri Mantras, with target Japa counts.
  5. Planetary Charity (Daan), Fasting (Vrata), and Yantra worship for malefic/afflicted planets.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Set

from .constants import SIGN_LORDS


# Yogakaraka planets for specific lagnas (rules both a Kendra and a Trikona)
YOGAKARAKA_LORDS = {
    2: "Saturn",   # Taurus: 9th & 10th
    4: "Mars",     # Cancer: 5th & 10th
    5: "Mars",     # Leo: 4th & 9th
    7: "Saturn",   # Libra: 4th & 5th
    10: "Venus",   # Capricorn: 5th & 10th
    11: "Venus",   # Aquarius: 4th & 9th
}

# Incompatible planetary gemstone pairs that must never be worn together
INCOMPATIBLE_PAIRS = [
    ({"Sun"}, {"Saturn", "Venus", "Rahu", "Ketu"}),
    ({"Moon"}, {"Rahu", "Ketu", "Saturn"}),
    ({"Mars"}, {"Mercury", "Saturn", "Rahu"}),
    ({"Mercury"}, {"Mars"}),
    ({"Jupiter"}, {"Venus", "Mercury"}),
    ({"Venus"}, {"Sun", "Moon", "Jupiter"}),
    ({"Saturn"}, {"Sun", "Moon", "Mars"}),
]

GEMSTONE_DATA = {
    "Sun": {
        "gemstone_ne": "माणिक्य (Ruby)",
        "gemstone_en": "Ruby (Manikya)",
        "upratna_ne": "गार्नेट (Garnet), रातो स्पिनल",
        "upratna_en": "Red Garnet, Red Spinel",
        "color_ne": "गाढा रातो / गुलावी",
        "color_en": "Deep Red / Pinkish Red",
        "metal_ne": "सुन वा तामा",
        "metal_en": "Gold or Copper",
        "finger_ne": "अनामिका (Ring Finger)",
        "finger_en": "Ring Finger (Anamika)",
        "day_ne": "आइतबार बिहान (शुक्ल पक्ष, सूर्योदय समय)",
        "day_en": "Sunday morning during Shukla Paksha at sunrise",
        "min_weight_ne": "५ देखि ७ रत्ती (वा शरीरको तौलको प्रति १० केजी १ रत्ती)",
        "min_weight_en": "5 to 7 Ratti (approx 1 ratti per 10kg body weight)",
        "beej_mantra": "ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः",
        "simple_mantra": "ॐ घृणिः सूर्याय नमः",
        "jap_count": "७,००० पटक",
        "jap_count_en": "7,000 times",
        "benefit_ne": "आत्मबल, मान-प्रतिष्ठा, नेतृत्व क्षमता, सरकारी काममा सफलता, र पितृ सुख वृद्धि गर्छ।",
        "benefit_en": "Enhances vitality, willpower, leadership, fatherly support, and government success."
    },
    "Moon": {
        "gemstone_ne": "मोती (Pearl)",
        "gemstone_en": "Pearl (Moti)",
        "upratna_ne": "मुनस्टोन (Moonstone)",
        "upratna_en": "Moonstone",
        "color_ne": "चम्किलो सेतो",
        "color_en": "Lustrous White",
        "metal_ne": "चाँदी",
        "metal_en": "Silver",
        "finger_ne": "कनिष्ठिका (Little Finger)",
        "finger_en": "Little Finger (Kanishthika)",
        "day_ne": "सोमबार साँझ वा बिहान (शुक्ल पक्ष)",
        "day_en": "Monday evening or morning during Shukla Paksha",
        "min_weight_ne": "५ देखि ८ रत्ती",
        "min_weight_en": "5 to 8 Ratti",
        "beej_mantra": "ॐ श्रां श्रीं श्रौं सः चन्द्रमसे नमः",
        "simple_mantra": "ॐ सों सोमाय नमः",
        "jap_count": "११,००० पटक",
        "jap_count_en": "11,000 times",
        "benefit_ne": "मानसिक शान्ति, एकाग्रता, मातृ सुख, भावनात्मक स्थिरता र रक्तसञ्चार सुधार गर्छ।",
        "benefit_en": "Improves mental tranquility, emotional stability, motherly harmony, and peace of mind."
    },
    "Mars": {
        "gemstone_ne": "मूंगा (Red Coral)",
        "gemstone_en": "Red Coral (Moonga)",
        "upratna_ne": "रातो अगेट (Red Carnelian)",
        "upratna_en": "Red Carnelian",
        "color_ne": "सिन्दुरे रातो",
        "color_en": "Vermilion / Deep Orange-Red",
        "metal_ne": "तामा वा सुन",
        "metal_en": "Copper or Gold",
        "finger_ne": "अनामिका (Ring Finger)",
        "finger_en": "Ring Finger (Anamika)",
        "day_ne": "मंगलबार बिहान (सूर्योदयको १ घण्टा भित्र)",
        "day_en": "Tuesday morning within 1 hour of sunrise",
        "min_weight_ne": "६ देखि ९ रत्ती",
        "min_weight_en": "6 to 9 Ratti",
        "beej_mantra": "ॐ क्रां क्रीं क्रौं सः भौमाय नमः",
        "simple_mantra": "ॐ अं अङ्गारकाय नमः",
        "jap_count": "१०,००० पटक",
        "jap_count_en": "10,000 times",
        "benefit_ne": "साहस, ऊर्जा, पराक्रम, जग्गाजमिन सम्बन्धी लाभ, र रक्त विकारबाट मुक्ति प्रदान गर्छ।",
        "benefit_en": "Boosts physical stamina, courage, real estate fortunes, and blood vitality."
    },
    "Mercury": {
        "gemstone_ne": "पन्ना (Emerald)",
        "gemstone_en": "Emerald (Panna)",
        "upratna_ne": "पेरिडट (Peridot), हरियो अनिक्स (Green Onyx)",
        "upratna_en": "Peridot, Green Onyx, Green Tourmaline",
        "color_ne": "गाढा हरियो",
        "color_en": "Vibrant Forest Green",
        "metal_ne": "सुन, काँस वा चाँदी",
        "metal_en": "Gold, Bronze or Silver",
        "finger_ne": "कनिष्ठिका (Little Finger)",
        "finger_en": "Little Finger (Kanishthika)",
        "day_ne": "बुधबार बिहान (शुक्ल पक्ष)",
        "day_en": "Wednesday morning during Shukla Paksha",
        "min_weight_ne": "४ देखि ६ रत्ती",
        "min_weight_en": "4 to 6 Ratti",
        "beej_mantra": "ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः",
        "simple_mantra": "ॐ बुं बुधाय नमः",
        "jap_count": "९,००० पटक",
        "jap_count_en": "9,000 times",
        "benefit_ne": "तीक्ष्ण बुद्धि, व्यापारिक सफलता, वाक-कला, शिक्षा तथा लेखा/सञ्चारमा उन्नति दिन्छ।",
        "benefit_en": "Sharpens intellect, business acumen, speech eloquence, and analytical abilities."
    },
    "Jupiter": {
        "gemstone_ne": "पुखराज (Yellow Sapphire)",
        "gemstone_en": "Yellow Sapphire (Pukhraj)",
        "upratna_ne": "पहेंलो टोपाज (Yellow Topaz), सुनौलो सिट्रीन (Citrine)",
        "upratna_en": "Yellow Topaz, Citrine",
        "color_ne": "हलेदो पहेंलो",
        "color_en": "Bright Golden Yellow",
        "metal_ne": "सुन वा पहेँलो धातु",
        "metal_en": "Gold or Brass",
        "finger_ne": "तर्जनी (Index Finger)",
        "finger_en": "Index Finger (Tarjani)",
        "day_ne": "बिहीबार बिहान (सूर्योदयको समयमा)",
        "day_en": "Thursday morning at sunrise",
        "min_weight_ne": "४ देखि ७ रत्ती",
        "min_weight_en": "4 to 7 Ratti",
        "beej_mantra": "ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः",
        "simple_mantra": "ॐ बृं बृहस्पतये नमः",
        "jap_count": "१९,००० पटक",
        "jap_count_en": "19,000 times",
        "benefit_ne": "ज्ञान, सन्तान सुख, विवाह सुख, आर्थिक समृद्धि, अध्यात्म र गुरु कृपा प्राप्त हुन्छ।",
        "benefit_en": "Attracts divine wisdom, marital bliss, wealth accumulation, and academic fortune."
    },
    "Venus": {
        "gemstone_ne": "हीरा (Diamond)",
        "gemstone_en": "Diamond (Heera)",
        "upratna_ne": "सेतो जिरकन (White Zircon), ओपल (Opal)",
        "upratna_en": "White Zircon, White Sapphire, Opal",
        "color_ne": "पारदर्शी / चम्किलो सेतो",
        "color_en": "Clear / Brilliant White",
        "metal_ne": "ह्वाइट गोल्ड, चाँदी वा प्लेटिनम",
        "metal_en": "White Gold, Silver or Platinum",
        "finger_ne": "कनिष्ठिका वा अनामिका",
        "finger_en": "Little Finger or Ring Finger",
        "day_ne": "शुक्रबार बिहान (शुक्ल पक्ष)",
        "day_en": "Friday morning during Shukla Paksha",
        "min_weight_ne": "०.५० देखि १.५ क्यारेट (ओपल भए ५-७ रत्ती)",
        "min_weight_en": "0.50 to 1.5 Carats (or 5-7 Ratti for Opal/Zircon)",
        "beej_mantra": "ॐ द्रां द्रीं द्रौं सः शुक्राय नमः",
        "simple_mantra": "ॐ शुं शुक्राय नमः",
        "jap_count": "१६,००० पटक",
        "jap_count_en": "16,000 times",
        "benefit_ne": "सौन्दर्य, विलासिता, कला, दाम्पत्य सुख, आकर्षण र भौतिक ऐश्वर्य वृद्धि गर्छ।",
        "benefit_en": "Enhances personal magnetism, artistic luxury, marital affection, and prosperity."
    },
    "Saturn": {
        "gemstone_ne": "नीलम (Blue Sapphire)",
        "gemstone_en": "Blue Sapphire (Neelam)",
        "upratna_ne": "एमेथिस्ट / जमुनिया (Amethyst), ब्लु टोपाज",
        "upratna_en": "Amethyst (Jamuniya), Blue Topaz, Iolite",
        "color_ne": "गाढा नीलो / इन्द्रनील",
        "color_en": "Deep Royal Blue",
        "metal_ne": "पञ्चधातु, चाँदी वा फलाम",
        "metal_en": "Panchadhatu, Silver or Iron",
        "finger_ne": "मध्यमा (Middle Finger)",
        "finger_en": "Middle Finger (Madhyama)",
        "day_ne": "शनिबार साँझ (सूर्यास्तपछि वा राहुकाल बाहेक)",
        "day_en": "Saturday evening after sunset",
        "min_weight_ne": "४ देखि ७ रत्ती (पहिले ३ दिन परीक्षण गरेर मात्र लगाउने)",
        "min_weight_en": "4 to 7 Ratti (test for 3 days under pillow before wearing)",
        "beej_mantra": "ॐ प्रां प्रीं प्रौं सः शनैश्चराय नमः",
        "simple_mantra": "ॐ शं शनैश्चराय नमः",
        "jap_count": "२३,००० पटक",
        "jap_count_en": "23,000 times",
        "benefit_ne": "अत्यन्त छिटो कार्य सिद्धि, न्याय, अनुसन्धान, दीर्घायु र साढेसातीको दुष्प्रभाव निवारण गर्छ।",
        "benefit_en": "Swift breakthrough in career, protection from accidents, justice, and Saturn adversity relief."
    },
    "Rahu": {
        "gemstone_ne": "गोमेद (Hessonite)",
        "gemstone_en": "Hessonite (Gomed)",
        "upratna_ne": "गोमेदक, खैरो जिरकन",
        "upratna_en": "Brown Zircon, Spessartite Garnet",
        "color_ne": "मह वा गाईको पिसाब जस्तो खैरो-रातो",
        "color_en": "Honey Colored / Brownish Red",
        "metal_ne": "चाँदी वा अष्टधातु",
        "metal_en": "Silver or Ashtadhatu",
        "finger_ne": "मध्यमा (Middle Finger)",
        "finger_en": "Middle Finger (Madhyama)",
        "day_ne": "शनिबार वा बुधबार राति",
        "day_en": "Saturday or Wednesday night",
        "min_weight_ne": "५ देखि ८ रत्ती",
        "min_weight_en": "5 to 8 Ratti",
        "beej_mantra": "ॐ भ्रां भ्रीं भ्रौं सः राहवे नमः",
        "simple_mantra": "ॐ रां राहवे नमः",
        "jap_count": "१८,००० पटक",
        "jap_count_en": "18,000 times",
        "benefit_ne": "आकस्मिक सफलता, राजनीति, विदेश यात्रा, र भ्रम/असुरक्षाको भावना हटाउन मद्दत गर्छ।",
        "benefit_en": "Sudden wealth breakthroughs, political elevation, foreign settlement, and clarity of mind."
    },
    "Ketu": {
        "gemstone_ne": "लहसुनिया (Cat's Eye)",
        "gemstone_en": "Cat's Eye (Vaidurya / Chrysoberyl)",
        "upratna_ne": "टाइगर आइ (Tiger Eye)",
        "upratna_en": "Tiger's Eye Quartz",
        "color_ne": "पहेंलो-हरियो बीचमा सेतो धागो जस्तो रेखा भएको",
        "color_en": "Greenish-yellow with a moving chatoyant band",
        "metal_ne": "चाँदी वा पञ्चधातु",
        "metal_en": "Silver or Panchadhatu",
        "finger_ne": "कनिष्ठिका वा अनामिका",
        "finger_en": "Little Finger or Ring Finger",
        "day_ne": "बिहीबार वा मंगलबार राति",
        "day_en": "Thursday or Tuesday night",
        "min_weight_ne": "४ देखि ६ रत्ती",
        "min_weight_en": "4 to 6 Ratti",
        "beej_mantra": "ॐ स्रां स्रीं स्रौं सः केतवे नमः",
        "simple_mantra": "ॐ कें केतवे नमः",
        "jap_count": "१७,००० पटक",
        "jap_count_en": "17,000 times",
        "benefit_ne": "आध्यात्मिक ज्ञान, मोक्ष, गुप्त विद्या, र शत्रु/शारीरिक कष्टबाट सुरक्षा प्रदान गर्छ।",
        "benefit_en": "Spiritual liberation, protection from concealed adversaries, intuition, and occult depth."
    }
}

RUDRAKSHA_DATA = {
    1: {
        "mukhi": "१ मुखी रुद्राक्ष",
        "mukhi_en": "1 Mukhi Rudraksha",
        "planet": "Sun",
        "deity_ne": "साक्षात् शिव (परमेश्वर)",
        "deity_en": "Lord Shiva (Supreme Consciousness)",
        "benefit_ne": "आत्मविश्वास, नेतृत्व, हृदय र आँखाको स्वास्थ्य, र सूर्य दोष निवारण।",
        "benefit_en": "Supreme leadership, self-realization, cardiovascular vitality, and Sun affliction relief.",
        "mantra": "ॐ ह्रीं नमः"
    },
    2: {
        "mukhi": "२ मुखी रुद्राक्ष",
        "mukhi_en": "2 Mukhi Rudraksha",
        "planet": "Moon",
        "deity_ne": "अर्धनारीश्वर (शिव-पार्वती)",
        "deity_en": "Ardhanarishwara (Shiva-Parvati)",
        "benefit_ne": "दाम्पत्य सुख, मानसिक शान्ति, भावनात्मक सन्तुलन, र चन्द्र दोष शान्ति।",
        "benefit_en": "Marital harmony, emotional stability, mental peace, and Moon affliction balance.",
        "mantra": "ॐ नमः"
    },
    3: {
        "mukhi": "३ मुखी रुद्राक्ष",
        "mukhi_en": "3 Mukhi Rudraksha",
        "planet": "Mars",
        "deity_ne": "अग्नि देव",
        "deity_en": "Agni Dev (Fire God)",
        "benefit_ne": "आलस्य मुक्ति, रक्त विकार निवारण, पराक्रम, र मंगल दोष शान्ति।",
        "benefit_en": "Eliminates lethargy, purifies blood vitality, bestows courage, and calms Manglik dosha.",
        "mantra": "ॐ क्लीं नमः"
    },
    4: {
        "mukhi": "४ मुखी रुद्राक्ष",
        "mukhi_en": "4 Mukhi Rudraksha",
        "planet": "Mercury",
        "deity_ne": "ब्रह्मा जी",
        "deity_en": "Lord Brahma",
        "benefit_ne": "विद्या, बुद्धि, स्मरण शक्ति, वाक-शक्ति, र बुध दोष निवारण।",
        "benefit_en": "Academic genius, memory expansion, vocal eloquence, and Mercury enhancement.",
        "mantra": "ॐ ह्रीं नमः"
    },
    5: {
        "mukhi": "५ मुखी रुद्राक्ष",
        "mukhi_en": "5 Mukhi Rudraksha",
        "planet": "Jupiter",
        "deity_ne": "कालाग्नि रुद्र",
        "deity_en": "Kalagni Rudra",
        "benefit_ne": "स्वास्थ्य, ज्ञान, रक्तचाप नियन्त्रण, गुरु कृपा, र सर्वकल्याण।",
        "benefit_en": "Overall health, blood pressure balance, wisdom, and Jupiter grace.",
        "mantra": "ॐ ह्रीं नमः"
    },
    6: {
        "mukhi": "६ मुखी रुद्राक्ष",
        "mukhi_en": "6 Mukhi Rudraksha",
        "planet": "Venus",
        "deity_ne": "कार्तिकेय जी",
        "deity_en": "Lord Kartikeya",
        "benefit_ne": "आकर्षण, कला, सन्तान सुख, इच्छा शक्ति, र शुक्र दोष शान्ति।",
        "benefit_en": "Willpower, charm, artistic flair, marital affection, and Venus blessing.",
        "mantra": "ॐ ह्रीं हुं नमः"
    },
    7: {
        "mukhi": "७ मुखी रुद्राक्ष",
        "mukhi_en": "7 Mukhi Rudraksha",
        "planet": "Saturn",
        "deity_ne": "महालक्ष्मी तथा सप्तर्षि",
        "deity_en": "Goddess Mahalakshmi",
        "benefit_ne": "आर्थिक स्थिरता, दरिद्रता निवारण, साढेसाती तथा शनि प्रकोप शान्ति।",
        "benefit_en": "Financial prosperity, alleviation of poverty, and Saturn / Sade Sati shield.",
        "mantra": "ॐ हुं नमः"
    },
    8: {
        "mukhi": "८ मुखी रुद्राक्ष",
        "mukhi_en": "8 Mukhi Rudraksha",
        "planet": "Rahu",
        "deity_ne": "गणेश जी",
        "deity_en": "Lord Ganesha",
        "benefit_ne": "विघ्न-बाधा निवारण, शत्रु नाश, आकस्मिक कष्ट मुक्ति, र राहु दोष शान्ति।",
        "benefit_en": "Obstacle removal, victory over adversity, and neutralizing Rahu malefic effects.",
        "mantra": "ॐ हुं नमः"
    },
    9: {
        "mukhi": "९ मुखी रुद्राक्ष",
        "mukhi_en": "9 Mukhi Rudraksha",
        "planet": "Ketu",
        "deity_ne": "माँ नवदुर्गा",
        "deity_en": "Goddess Navadurga",
        "benefit_ne": "साहस, भयमुक्ति, ऊर्जा, आध्यात्मिक शक्ति, र केतु दोष निवारण।",
        "benefit_en": "Fearlessness, dynamic vigor, spiritual grounding, and Ketu stabilization.",
        "mantra": "ॐ ह्रीं हुं नमः"
    },
    10: {
        "mukhi": "१० मुखी रुद्राक्ष",
        "mukhi_en": "10 Mukhi Rudraksha",
        "planet": "All",
        "deity_ne": "भगवान् विष्णु",
        "deity_en": "Lord Vishnu",
        "benefit_ne": "दश दिशाबाट रक्षा, कानुनी झमेला निवारण, नकारात्मक ऊर्जाबाट पूर्ण सुरक्षा।",
        "benefit_en": "Protection in all 10 directions, legal immunity, and banishing dark energies.",
        "mantra": "ॐ ह्रीं नमः"
    },
    11: {
        "mukhi": "११ मुखी रुद्राक्ष",
        "mukhi_en": "11 Mukhi Rudraksha",
        "planet": "Mars/Jupiter",
        "deity_ne": "एकादश रुद्र (हनुमान जी)",
        "deity_en": "Lord Hanuman (11 Rudras)",
        "benefit_ne": "अदम्य साहस, निर्णय क्षमता, व्यापारिक वृद्धि, र योग-साधनामा सिद्धि।",
        "benefit_en": "Indomitable courage, physical endurance, business victory, and meditative focus.",
        "mantra": "ॐ ह्रीं हुं नमः"
    },
    12: {
        "mukhi": "१२ मुखी रुद्राक्ष",
        "mukhi_en": "12 Mukhi Rudraksha",
        "planet": "Sun",
        "deity_ne": "द्वादश आदित्य (भगवान् सूर्य)",
        "deity_en": "12 Adityas (Solar Sovereignty)",
        "benefit_ne": "तेजस्विता, प्रशासकीय उच्च पद, रोग मुक्ति, र सम्पूर्ण सूर्य कृपा।",
        "benefit_en": "Radiance, executive authority, vitality, and solar empowerment.",
        "mantra": "ॐ क्रौं क्षौं रौं नमः"
    },
    13: {
        "mukhi": "१३ मुखी रुद्राक्ष",
        "mukhi_en": "13 Mukhi Rudraksha",
        "planet": "Venus",
        "deity_ne": "कामदेव तथा इन्द्र",
        "deity_en": "Lord Kamadeva and Indra",
        "benefit_ne": "आकर्षण, कामसुख, आकर्षण शक्ति, र सबै प्रकारको भोग-ऐश्वर्य सिद्धि।",
        "benefit_en": "Hypnotic charisma, magnetic social attraction, and sensory luxuries.",
        "mantra": "ॐ ह्रीं नमः"
    },
    14: {
        "mukhi": "१४ मुखी रुद्राक्ष (देवमणि)",
        "mukhi_en": "14 Mukhi Rudraksha (Devamani)",
        "planet": "Saturn",
        "deity_ne": "साक्षात् भगवान् शिव (महादेव)",
        "deity_en": "Lord Shiva (Ajna Chakra)",
        "benefit_ne": "दिव्य दृष्टि, छैटौं इन्द्रिय (Sixth Sense) जागरण, र शनि/मंगल दोषको महा-कवच।",
        "benefit_en": "Sixth sense activation, supreme intuition, and invincible planetary armor.",
        "mantra": "ॐ नमः"
    }
}

CHARITY_AND_FASTING = {
    "Sun": {
        "charity_items_ne": "गहुँ, गुड (सख्खर), रातो कपडा, तामाको भाँडो, माणिक्य, वा रातो गाई।",
        "charity_items_en": "Wheat, jaggery, red cloth, copper vessel, red flowers.",
        "charity_recipient_ne": "विद्वान् ब्राह्मण वा मन्दिरका पुजारी।",
        "charity_recipient_en": "Scholarly priest or noble temple custodian.",
        "fasting_day_ne": "आइतबार (नुन नखाई फलफूल र खीर खाने)।",
        "fasting_day_en": "Sunday (avoid salt; consume milk and fruits).",
        "yantra_ne": "सूर्य यन्त्र",
        "yantra_en": "Surya Yantra",
        "gayatri_mantra": "ॐ आदित्याय विद्महे प्रभाकराय धीमहि तन्नः सूर्यः प्रचोदयात्।"
    },
    "Moon": {
        "charity_items_ne": "चामल, दूध, चाँदी, सेतो कपडा, शङ्ख, सेतो मिठाई वा कपूर।",
        "charity_items_en": "Rice, milk, silver, white garments, conch shell, white sweets.",
        "charity_recipient_ne": "वृद्धा महिला, माता समानकी नारी वा गरिब व्यक्ति।",
        "charity_recipient_en": "Elderly women, motherly figures, or vulnerable destitute individuals.",
        "fasting_day_ne": "सोमबार (शिवजीको आराधनासहित)।",
        "fasting_day_en": "Monday (with Lord Shiva worship).",
        "yantra_ne": "चन्द्र यन्त्र",
        "yantra_en": "Chandra Yantra",
        "gayatri_mantra": "ॐ क्षीरपुत्राय विद्महे अमृतत्त्वाय धीमहि तन्नो चन्द्रः प्रचोदयात्।"
    },
    "Mars": {
        "charity_items_ne": "मसुरोको दाल, गुड, रातो चन्दन, तामा, सिन्दुर वा रातो मिठाई।",
        "charity_items_en": "Red lentils (Masoor dal), jaggery, red sandalwood, copper, vermilion.",
        "charity_recipient_ne": "भाइ-साथी, ब्रह्मचारी वा सेना/प्रहरी सम्बद्ध व्यक्ति।",
        "charity_recipient_en": "Celibates, younger brothers, or service warriors.",
        "fasting_day_ne": "मंगलबार (हनुमान चालीसा पाठसहित)।",
        "fasting_day_en": "Tuesday (with recitation of Hanuman Chalisa).",
        "yantra_ne": "मंगल यन्त्र",
        "yantra_en": "Mangal Yantra",
        "gayatri_mantra": "ॐ अङ्गारकाय विद्महे शक्तिहस्ताय धीमहि तन्नो भौमः प्रचोदयात्।"
    },
    "Mercury": {
        "charity_items_ne": "मुँगको दाल, हरियो कपडा, काँसको भाँडो, हरियो तरकारी, फलफूल वा पुस्तक।",
        "charity_items_en": "Moong dal, green cloth, bronze utensils, green vegetables, books.",
        "charity_recipient_ne": "विद्यार्थी, बालबालिका, वा बहिनी/फुपू।",
        "charity_recipient_en": "Needy students, young children, or sisters.",
        "fasting_day_ne": "बुधबार (गणेश जीको पूजासहित)।",
        "fasting_day_en": "Wednesday (with Lord Ganesha worship).",
        "yantra_ne": "बुध यन्त्र",
        "yantra_en": "Budha Yantra",
        "gayatri_mantra": "ॐ सौम्यरूपाय विद्महे वाणेशाय धीमहि तन्नो सौम्यः प्रचोदयात्।"
    },
    "Jupiter": {
        "charity_items_ne": "चनाको दाल, बेसार, पहेंलो कपडा, सुन, केरा, मह वा धार्मिक ग्रन्थ।",
        "charity_items_en": "Gram dal (Chana dal), turmeric, yellow cloth, gold, bananas, scriptures.",
        "charity_recipient_ne": "गुरु, शिक्षक, विद्वान् वा साधु-सन्त।",
        "charity_recipient_en": "Spiritual teachers, scholars, mentors, or sages.",
        "fasting_day_ne": "बिहीबार (पहेंलो भोजन गर्ने र केराको रुखको पूजा)।",
        "fasting_day_en": "Thursday (consume yellow food, worship banana tree).",
        "yantra_ne": "बृहस्पति यन्त्र",
        "yantra_en": "Guru Yantra",
        "gayatri_mantra": "ॐ वृषभध्वजाय विद्महे घृणिहस्ताय धीमहि तन्नो गुरुः प्रचोदयात्।"
    },
    "Venus": {
        "charity_items_ne": "घिउ, दही, खीर, चाँदी, सेतो रेशमी कपडा, सुगन्धित वस्तु (अत्तर)।",
        "charity_items_en": "Pure ghee, curd, rice pudding, silver, white silk, perfumes.",
        "charity_recipient_ne": "कन्या, विवाहित महिला वा कलाकर्मी।",
        "charity_recipient_en": "Young girls, auspicious married women, or artists.",
        "fasting_day_ne": "शुक्रबार (महालक्ष्मी वा सन्तोषी माताको व्रत)।",
        "fasting_day_en": "Friday (worship Goddess Mahalakshmi or Santoshi Mata).",
        "yantra_ne": "शुक्र यन्त्र",
        "yantra_en": "Shukra Yantra",
        "gayatri_mantra": "ॐ भृगुजाय विद्महे दिव्यदेहाय धीमहि तन्नः शुक्रः प्रचोदयात्।"
    },
    "Saturn": {
        "charity_items_ne": "कालो तिल, तोरीको तेल, फलामको भाँडो, कालो कपडा, छाता वा जुत्ता।",
        "charity_items_en": "Black sesame seeds, mustard oil, iron utensils, black blanket, footwear.",
        "charity_recipient_ne": "श्रमिक, असहाय, अशक्त वा गरिब व्यक्ति।",
        "charity_recipient_en": "Hardworking laborers, destitute elders, or disabled individuals.",
        "fasting_day_ne": "शनिबार (पीपलको रुखमा पानी चढाउने र दियो बाल्ने)।",
        "fasting_day_en": "Saturday (light mustard oil lamp under Peepal tree).",
        "yantra_ne": "शनि यन्त्र",
        "yantra_en": "Shani Yantra",
        "gayatri_mantra": "ॐ काकध्वजाय विद्महे खड्गहस्ताय धीमहि तन्नो मन्दः प्रचोदयात्।"
    },
    "Rahu": {
        "charity_items_ne": "उरादको दाल, कालो/नीलो कपडा, नरिवल, सख्खर, फलाम वा सिक्का।",
        "charity_items_en": "Urad dal, smoky blue cloth, dry coconut, lead metal, old coins.",
        "charity_recipient_ne": "सफाइकर्मी वा कुष्ठरोगी।",
        "charity_recipient_en": "Sanitation workers or lepers.",
        "fasting_day_ne": "शनिबार वा बुधबार (भैरव जी वा सरस्वती पूजा)।",
        "fasting_day_en": "Saturday or Wednesday (worship Lord Bhairava or Saraswati).",
        "yantra_ne": "राहु यन्त्र",
        "yantra_en": "Rahu Yantra",
        "gayatri_mantra": "ॐ नागाधिपाय विद्महे सर्पमुख्याय धीमहि तन्नो राहुः प्रचोदयात्।"
    },
    "Ketu": {
        "charity_items_ne": "दुई रंगको (कालो-सेतो) कम्बल, तिल, कागती, लसुन वा कुकुरलाई रोटी।",
        "charity_items_en": "Two-tone (black & white) blanket, sesame, lemon, feeding stray dogs.",
        "charity_recipient_ne": "अनाथालय, वृद्धश्रम वा कुकुरलाई खुवाउने।",
        "charity_recipient_en": "Orphanages, destitute shelters, or feeding street dogs.",
        "fasting_day_ne": "मंगलबार वा बिहीबार (गणेश जीको संकष्ट चतुर्थी)।",
        "fasting_day_en": "Tuesday or Thursday (worship Lord Ganesha on Sankashti Chaturthi).",
        "yantra_ne": "केतु यन्त्र",
        "yantra_en": "Ketu Yantra",
        "gayatri_mantra": "ॐ अश्मध्वजाय विद्महे शूलहस्ताय धीमहि तन्नो केतुः प्रचोदयात्।"
    }
}


def _get_house_lord(lagna_sign: int, house_num: int) -> str:
    """Return the planetary lord of a given house (1-12) from Lagna."""
    sign = (lagna_sign + house_num - 2) % 12 + 1
    return SIGN_LORDS[sign]


def calculate_remedies(
    planets_data: List[Dict[str, Any]],
    lagna_sign_num: int,
    dasha_data: Optional[List[Dict[str, Any]]] = None,
    language: str = "ne"
) -> Dict[str, Any]:
    """
    Calculate comprehensive Vedic remedies:
      - Gemstone recommendations (Life, Lucky, Punya/Knowledge, Yogakaraka)
      - Strictly forbidden gemstones and incompatible combinations
      - Rudraksha recommendations (1-14 Mukhi)
      - Vedic & Tantrik Mantras, Gayatri Mantras
      - Planetary charity, fasting, and yantras
    """
    is_ne = language == "ne"

    # 1. Identify Key House Lords
    lagna_lord = _get_house_lord(lagna_sign_num, 1)
    fifth_lord = _get_house_lord(lagna_sign_num, 5)
    ninth_lord = _get_house_lord(lagna_sign_num, 9)
    yogakaraka_lord = YOGAKARAKA_LORDS.get(lagna_sign_num)

    # 2. Identify Trik House Lords (6, 8, 12)
    sixth_lord = _get_house_lord(lagna_sign_num, 6)
    eighth_lord = _get_house_lord(lagna_sign_num, 8)
    twelfth_lord = _get_house_lord(lagna_sign_num, 12)

    # 3. Identify Maraka House Lords (2, 7)
    second_lord = _get_house_lord(lagna_sign_num, 2)
    seventh_lord = _get_house_lord(lagna_sign_num, 7)

    # Trik set
    trik_lords = {sixth_lord, eighth_lord, twelfth_lord}
    # Trikona set (1, 5, 9) - these planets are inherently auspicious
    trikona_lords = {lagna_lord, fifth_lord, ninth_lord}
    if yogakaraka_lord:
        trikona_lords.add(yogakaraka_lord)

    # Strictly forbidden planets to wear gemstones for:
    # Any planet ruling 6, 8, 12 that does NOT rule a trikona or lagna
    forbidden_planets: Set[str] = set()
    for p in trik_lords:
        if p not in trikona_lords:
            forbidden_planets.add(p)

    # Rahu / Ketu caution: Only wear if well placed, otherwise forbidden by default
    # in classical Parashari unless specific Raja yoga applies.
    forbidden_planets.add("Rahu")
    forbidden_planets.add("Ketu")

    # 4. Compile Recommended Gemstones
    recommended_gemstones: List[Dict[str, Any]] = []

    # Helper to construct gemstone recommendation dict
    def _make_gem_rec(category_code: str, category_label_ne: str, category_label_en: str, planet: str) -> Dict[str, Any]:
        info = GEMSTONE_DATA.get(planet, {})
        return {
            "category_code": category_code,
            "category_name": category_label_ne if is_ne else category_label_en,
            "planet": planet,
            "gemstone": info.get("gemstone_ne" if is_ne else "gemstone_en", ""),
            "upratna": info.get("upratna_ne" if is_ne else "upratna_en", ""),
            "color": info.get("color_ne" if is_ne else "color_en", ""),
            "metal": info.get("metal_ne" if is_ne else "metal_en", ""),
            "finger": info.get("finger_ne" if is_ne else "finger_en", ""),
            "day": info.get("day_ne" if is_ne else "day_en", ""),
            "min_weight": info.get("min_weight_ne" if is_ne else "min_weight_en", ""),
            "beej_mantra": info.get("beej_mantra", ""),
            "simple_mantra": info.get("simple_mantra", ""),
            "jap_count": info.get("jap_count" if is_ne else "jap_count_en", ""),
            "benefit": info.get("benefit_ne" if is_ne else "benefit_en", ""),
            "priority": "HIGH" if category_code in ("life_stone", "yogakaraka_stone") else "MEDIUM"
        }

    # Life Stone (Lagna Lord)
    recommended_gemstones.append(
        _make_gem_rec("life_stone", "जीवन रत्न (लग्नेश)", "Life Stone (Ascendant Lord)", lagna_lord)
    )

    # Lucky Stone (9th Lord)
    if ninth_lord != lagna_lord:
        recommended_gemstones.append(
            _make_gem_rec("lucky_stone", "भाग्य रत्न (नवमेश)", "Lucky Stone (9th Lord)", ninth_lord)
        )

    # Knowledge / Benefic Stone (5th Lord)
    if fifth_lord not in (lagna_lord, ninth_lord):
        recommended_gemstones.append(
            _make_gem_rec("punya_stone", "ज्ञान/संतान रत्न (पञ्चमेश)", "Punya/Knowledge Stone (5th Lord)", fifth_lord)
        )

    # Yogakaraka Stone (if applicable)
    if yogakaraka_lord and yogakaraka_lord not in (lagna_lord, ninth_lord, fifth_lord):
        recommended_gemstones.append(
            _make_gem_rec("yogakaraka_stone", "राजयोगकारक रत्न", "Yogakaraka Royal Stone", yogakaraka_lord)
        )

    # 5. Compile Forbidden Gemstones with specific reasons
    forbidden_list: List[Dict[str, Any]] = []
    for fp in sorted(forbidden_planets):
        info = GEMSTONE_DATA.get(fp, {})
        gem_name = info.get("gemstone_ne" if is_ne else "gemstone_en", fp)
        if fp in ("Rahu", "Ketu"):
            reason_ne = f"{fp} छाया ग्रह भएको र कुण्डलीमा पापकर्मकारक हुने सम्भावना भएकाले विशेष दशा/परामर्श बिना यसको रत्न नलगाउनु होला।"
            reason_en = f"{fp} is a shadowy karmic node; its gemstone should not be worn without specific expert astrological guidance."
        else:
            reason_ne = f"{fp} यस कुण्डलीका लागि त्रिक भाव (६, ८ वा १२ भाव) को अधिपति भएकाले यसको रत्न लगाउँदा रोग, ऋण, शत्रु वा हानि बढ्न सक्छ।"
            reason_en = f"{fp} rules trik houses (6th, 8th or 12th) for this ascendant; strengthening it can increase debts, health issues, or losses."

        forbidden_list.append({
            "planet": fp,
            "gemstone": gem_name,
            "reason": reason_ne if is_ne else reason_en
        })

    # Incompatible combinations warning
    rec_planets = {g["planet"] for g in recommended_gemstones}
    conflict_warnings: List[str] = []
    for group_a, group_b in INCOMPATIBLE_PAIRS:
        overlap_a = group_a.intersection(rec_planets)
        overlap_b = group_b.intersection(rec_planets)
        if overlap_a and overlap_b:
            p_a = list(overlap_a)[0]
            p_b = list(overlap_b)[0]
            gem_a = GEMSTONE_DATA.get(p_a, {}).get("gemstone_ne" if is_ne else "gemstone_en", p_a)
            gem_b = GEMSTONE_DATA.get(p_b, {}).get("gemstone_ne" if is_ne else "gemstone_en", p_b)
            if is_ne:
                conflict_warnings.append(f"चेतावनी: {gem_a} र {gem_b} एकआपसमा शत्रु ग्रहका रत्न हुन्। यी दुवै रत्न एउटै समयमा कदापि नलगाउनु होला।")
            else:
                conflict_warnings.append(f"Caution: {gem_a} and {gem_b} belong to hostile planets; they should NEVER be worn simultaneously.")

    # 6. Rudraksha Recommendations
    # Based on Lagna lord, Moon nakshatra, and afflicted planets
    rudraksha_recommendations: List[Dict[str, Any]] = []

    # Map planet to primary mukhi
    planet_to_mukhi = {
        "Sun": 1, "Moon": 2, "Mars": 3, "Mercury": 4,
        "Jupiter": 5, "Venus": 6, "Saturn": 7, "Rahu": 8, "Ketu": 9
    }

    # A) Primary Rudraksha based on Lagnesha
    lagna_mukhi = planet_to_mukhi.get(lagna_lord, 5)
    r_info = RUDRAKSHA_DATA.get(lagna_mukhi, {})
    rudraksha_recommendations.append({
        "type": "lagna_rudraksha",
        "title": "आधारभूत जीवन रुद्राक्ष (लग्नेश)" if is_ne else "Primary Life Rudraksha (Ascendant Lord)",
        "mukhi": r_info.get("mukhi" if is_ne else "mukhi_en"),
        "planet": lagna_lord,
        "deity": r_info.get("deity_ne" if is_ne else "deity_en"),
        "benefit": r_info.get("benefit_ne" if is_ne else "benefit_en"),
        "mantra": r_info.get("mantra")
    })

    # B) Secondary Rudraksha based on 9th Lord (Fortune)
    ninth_mukhi = planet_to_mukhi.get(ninth_lord, 5)
    if ninth_mukhi != lagna_mukhi:
        r_info9 = RUDRAKSHA_DATA.get(ninth_mukhi, {})
        rudraksha_recommendations.append({
            "type": "fortune_rudraksha",
            "title": "भाग्य वृद्धि रुद्राक्ष (भाग्येश)" if is_ne else "Fortune Rudraksha (9th Lord)",
            "mukhi": r_info9.get("mukhi" if is_ne else "mukhi_en"),
            "planet": ninth_lord,
            "deity": r_info9.get("deity_ne" if is_ne else "deity_en"),
            "benefit": r_info9.get("benefit_ne" if is_ne else "benefit_en"),
            "mantra": r_info9.get("mantra")
        })

    # C) Afflicted / Weak planets Rudraksha
    # Check combust, debilitated, or 6/8/12 placed planets
    added_mukhi = {lagna_mukhi, ninth_mukhi}
    for p in planets_data:
        p_name = p.get("name")
        if p_name not in planet_to_mukhi:
            continue
        is_debilitated = p.get("exaltation_state") == "DEBILITATED"
        is_combust = p.get("is_combust", False)
        house = p.get("house", 1)
        in_trik = house in (6, 8, 12)

        if (is_debilitated or is_combust or in_trik) and p_name != lagna_lord:
            m = planet_to_mukhi[p_name]
            if m not in added_mukhi:
                r_m = RUDRAKSHA_DATA.get(m, {})
                cond_label = "नीच" if is_debilitated else ("अस्त" if is_combust else "त्रिक भाव")
                cond_label_en = "Debilitated" if is_debilitated else ("Combust" if is_combust else "Trik House")
                rudraksha_recommendations.append({
                    "type": "affliction_rudraksha",
                    "title": f"ग्रह शान्ति रुद्राक्ष ({p_name} - {cond_label})" if is_ne else f"Planetary Shield Rudraksha ({p_name} - {cond_label_en})",
                    "mukhi": r_m.get("mukhi" if is_ne else "mukhi_en"),
                    "planet": p_name,
                    "deity": r_m.get("deity_ne" if is_ne else "deity_en"),
                    "benefit": r_m.get("benefit_ne" if is_ne else "benefit_en"),
                    "mantra": r_m.get("mantra")
                })
                added_mukhi.add(m)

    # D) All-round universal shield: 5 Mukhi (Pancha Mukhi) if not already included
    if 5 not in added_mukhi:
        r5 = RUDRAKSHA_DATA.get(5, {})
        rudraksha_recommendations.append({
            "type": "universal_rudraksha",
            "title": "सर्वकल्याण रुद्राक्ष (आरोग्य र शान्ति)" if is_ne else "Universal Health & Peace Rudraksha",
            "mukhi": r5.get("mukhi" if is_ne else "mukhi_en"),
            "planet": "Jupiter",
            "deity": r5.get("deity_ne" if is_ne else "deity_en"),
            "benefit": r5.get("benefit_ne" if is_ne else "benefit_en"),
            "mantra": r5.get("mantra")
        })

    # 7. Mantras, Charity, and Fasting for Planets
    mantras_and_charity_list: List[Dict[str, Any]] = []
    # Always include all 9 traditional planets in order
    nine_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    for p_name in nine_planets:
        c_info = CHARITY_AND_FASTING.get(p_name, {})
        g_info = GEMSTONE_DATA.get(p_name, {})
        mantras_and_charity_list.append({
            "planet": p_name,
            "beej_mantra": g_info.get("beej_mantra", ""),
            "simple_mantra": g_info.get("simple_mantra", ""),
            "gayatri_mantra": c_info.get("gayatri_mantra", ""),
            "jap_count": g_info.get("jap_count" if is_ne else "jap_count_en", ""),
            "charity_items": c_info.get("charity_items_ne" if is_ne else "charity_items_en", ""),
            "charity_recipient": c_info.get("charity_recipient_ne" if is_ne else "charity_recipient_en", ""),
            "fasting_day": c_info.get("fasting_day_ne" if is_ne else "fasting_day_en", ""),
            "yantra": c_info.get("yantra_ne" if is_ne else "yantra_en", "")
        })

    return {
        "recommended_gemstones": recommended_gemstones,
        "forbidden_gemstones": forbidden_list,
        "conflict_warnings": conflict_warnings,
        "rudraksha_recommendations": rudraksha_recommendations,
        "mantras_and_charity": mantras_and_charity_list,
        "general_guidelines": [
            "कुनै पनि रत्न धारण गर्नु अघि योग्य ज्योतिषीबाट कुण्डली परीक्षण गराउनुहोला।" if is_ne else "Always verify horoscope strength with a qualified astrologer before wearing precious gemstones.",
            "रत्न सधैं प्राकृतिक (Natural), शुद्ध (Untreated) र निर्दोष (Flawless) हुनुपर्छ; फुटेको वा खोट भएको रत्नले उल्टो फल दिन्छ।" if is_ne else "Gemstones must be natural, unheated, and free of visible cracks/flaws.",
            "रत्न लगाउँदा सम्बन्धित ग्रहको मन्त्र १०८ पटक जप गरी, पञ्चामृत र गंगाजलले शुद्ध गरेर मात्र धारण गर्नुहोस्।" if is_ne else "Energize gemstones by chanting the respective beej mantra 108 times and purifying with Panchamrita/holy water."
        ]
    }
