# -*- coding: utf-8 -*-
"""Comprehensive Nepali User Guide & Kundali Data Input Guidelines Dialog.

Provides an interactive, searchable reference for birth data entry rules,
midnight boundaries, foreign birth timezone conversion, DST handling,
and navigating all astrological analysis sections.
"""
from __future__ import annotations

from typing import Optional
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon, QColor
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QTextBrowser, QPushButton, QSplitter,
    QFrame, QScrollArea
)

# Visual style tokens
COLOR_GOLD = "#d4af37"
COLOR_PRIMARY = "#8b1e0f"
BG_DARK = "#1a1614"
BG_CARD = "#241e1a"
BORDER_COLOR = "#3d322a"
TEXT_PRIMARY = "#f5f0eb"
TEXT_MUTED = "#a89f91"


GUIDE_TOPICS = [
    {
        "id": "intro_rules",
        "title": "१. जन्म मिति र समय राख्ने मुख्य नियम (Civil Date & 24-Hour Format)",
        "keywords": "नियम मिति समय गते राती १२ बजे २४ घण्टा am pm format civil date",
        "html": """
        <h2 style="color: #d4af37;">१. जन्म मिति र समय राख्ने मुख्य नियम (Civil Date & 24-Hour Format)</h2>
        <p style="font-size: 14px; line-height: 1.6;">
            कुण्डली सफ्टवेयरले अन्तर्राष्ट्रिय तथा शास्त्रीय खगोलीय नियम अनुसार <b>मध्यरात १२:०० (००:००) देखि अर्को मध्यरात १२:०० सम्मको क्यालेन्डर मिति (Civil Date)</b> प्रयोग गर्दछ।
        </p>
        
        <div style="background-color: #2b221b; border-left: 4px solid #d4af37; padding: 12px; margin: 15px 0;">
            <b style="color: #e5c158; font-size: 15px;">⚠️ मध्यरात पछिको जन्म (राती १२ बजेपछि) मा ध्यान दिनुपर्ने कुरा:</b>
            <p style="margin: 6px 0 0 0; line-height: 1.5;">
                नेपाली समाजमा बोलचालमा राती सुत्नु अघिको मिति नै भन्ने चलन छ (जस्तै: <i>"बैशाख ५ गते राती १:१५ बजे जन्मियो"</i>)। 
                तर घडी र क्यालेन्डर अनुसार मध्यरात १२:०० कटिसकेपछि <b>६ गते</b> सुरु भइसकेको हुन्छ। त्यसैले १२ बजेपछिको १:१५ बजेलाई <b>६ गते 01:15:00</b> राख्नुपर्छ।
            </p>
        </div>

        <h3 style="color: #e5c158;">समय ढाँचा (24-Hour vs AM/PM):</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; border-color: #44372c; margin-top: 10px;">
            <tr style="background-color: #352a22; color: #d4af37;">
                <th>वास्तविक जन्म समय</th>
                <th>२४ घण्टे ढाँचा (24-Hour)</th>
                <th>AM / PM ढाँचा</th>
            </tr>
            <tr>
                <td>मध्यरातपछिको १:१५ (राती १:१५)</td>
                <td><b>01:15:00</b></td>
                <td>01:15 AM</td>
            </tr>
            <tr style="background-color: #241e1a;">
                <td>बिहानको ०६:३० बजे</td>
                <td><b>06:30:00</b></td>
                <td>06:30 AM</td>
            </tr>
            <tr>
                <td>दिउँसोको १:१५ बजे</td>
                <td><b>13:15:00</b></td>
                <td>01:15 PM</td>
            </tr>
            <tr style="background-color: #241e1a;">
                <td>बेलुकाको ०७:४५ बजे</td>
                <td><b>19:45:00</b></td>
                <td>07:45 PM</td>
            </tr>
            <tr>
                <td>रातीको ११:१५ बजे (मध्यरात अगाडि)</td>
                <td><b>23:15:00</b></td>
                <td>11:15 PM</td>
            </tr>
        </table>

        <h3 style="color: #e5c158; margin-top: 20px;">उदाहरण सहित स्पष्ट विवरण:</h3>
        <p><b>उदाहरण १:</b> यदि ५ गतेको दिनभरि सकिएर राती सुतेपछि (मध्यरात १२ बजेपछिको १:१५ बजे) जन्म भएको हो भने:</p>
        <ul>
            <li><b>जन्म मिति:</b> २०८३ बैशाख ०६ गते (2083-01-06)</li>
            <li><b>जन्म समय:</b> 01:15:00 (वा 01:15 AM)</li>
        </ul>
        <p><b>उदाहरण २:</b> यदि ४ गतेको दिनभरि सकिएर राती सुतेपछि ५ गते सुरु हुँदाको १:१५ बजे जन्म भएको हो भने:</p>
        <ul>
            <li><b>जन्म मिति:</b> २०८३ बैशाख ०५ गते (2083-01-05)</li>
            <li><b>जन्म समय:</b> 01:15:00 (वा 01:15 AM)</li>
        </ul>
        """
    },
    {
        "id": "foreign_birth",
        "title": "२. विदेशमा जन्मिएका व्यक्तिको डेटा इन्पुट (USA, UK, Australia, Gulf)",
        "keywords": "विदेश अमेरिका क्यानडा अस्ट्रेलिया खाडी युके युएसए dst daylight saving timezone local time गोल्डेन रुल",
        "html": """
        <h2 style="color: #d4af37;">२. विदेशमा जन्मिएका व्यक्तिको डेटा इन्पुट र टाइमजोन नियम</h2>
        <p style="font-size: 14px; line-height: 1.6;">
            विदेश (जस्तै: अमेरिका, क्यानडा, अस्ट्रेलिया, युरोप, खाडी मुलुक) मा जन्मिएका जातकको कुण्डली बनाउँदा 
            <b>सधैं बच्चा जन्मिएको स्थानको स्थानीय मिति र स्थानीय घडीको समय (Local Standard Time of Birthplace)</b> राख्नुपर्दछ, नेपालको समय होइन।
        </p>

        <div style="background-color: #3b2a1a; border-left: 4px solid #ffaa00; padding: 14px; margin: 15px 0; border-radius: 4px;">
            <b style="color: #ffcc00; font-size: 16px;">⭐ गोल्डेन रुल: जातक जुन स्थानमा जन्मिएको हो, सोही स्थानको स्थानीय समय र मिति हाल्नुपर्छ!</b>
            <p style="margin: 8px 0 0 0; line-height: 1.6; font-size: 14px;">
                कुण्डली निर्माण गर्दा <b>सधैं बच्चा जन्मिएको अस्पताल वा स्थानको घडीमा जे स्थानीय मिति र समय छ, त्यही हाल्नुपर्दछ</b>। 
                उदाहरणका लागि: यदि बच्चा अमेरिका, जापान वा अस्ट्रेलियामा जन्मिएको छ भने त्यहाँको स्थानीय समय राख्नुपर्छ, नेपालको समय हाल्न हुँदैन।
            </p>
        </div>

        <div style="background-color: #3b1b1b; border-left: 4px solid #ff6b6b; padding: 12px; margin: 15px 0;">
            <b style="color: #ff9999; font-size: 15px;">🚨 किन नेपालको समय राख्न हुँदैन?</b>
            <p style="margin: 6px 0 0 0; line-height: 1.5;">
                कुण्डलीको <b>लग्न (Ascendant)</b> भनेको जातक जन्मिएको क्षणमा उक्त स्थानको पूर्वी क्षितिजमा उदाउँदै गरेको राशि हो।
                यदि अमेरिकाको जन्ममा नेपालको समय राख्नुभयो भने लग्न ५ देखि ६ राशिले नै गल्ती हुन्छ र सम्पूर्ण कुण्डली बिग्रिन्छ।
            </p>
        </div>

        <h3 style="color: #e5c158;">डेलाइट सेभिङ टाइम (Daylight Saving Time - DST) व्यवस्था:</h3>
        <p>
            अमेरिका, युरोप, क्यानडा, अस्ट्रेलिया आदि देशहरूमा जाडो र गर्मी महिना अनुसार १ घण्टा समय परिवर्तन हुन्छ।
            हाम्रो इन्जिनले आधिकारिक <b>IANA zoneinfo</b> डाटाबेस प्रयोग गरी जन्म मितिका आधारमा DST स्वतः हिसाब गर्दछ। 
            तपाईंले अस्पतालको जन्म प्रमाणपत्रमा जे समय लेखिएको छ, त्यही सिधै राख्दा पुग्छ।
        </p>

        <h3 style="color: #e5c158;">नेपाल समयबाट अमेरिका समय रूपान्तरण उदाहरण:</h3>
        <p>यदि कसैले <i>"नेपालमा २०८३ बैशाख ६ गते बिहान ०१:१५ (१९ अप्रिल २०२६ ०१:१५) हुँदा अमेरिकामा बच्चा जन्मियो"</i> भन्यो भने:</p>
        
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; border-color: #44372c;">
            <tr style="background-color: #352a22; color: #d4af37;">
                <th>अमेरिकाको सहर / राज्य</th>
                <th>नेपाल भन्दा फरक</th>
                <th>सफ्टवेयरमा राख्ने मिति र समय (AD)</th>
            </tr>
            <tr>
                <td><b>New York / Washington DC / Boston</b> (EDT)</td>
                <td>९ घण्टा ४५ मिनेट पछाडि</td>
                <td><b>2026-04-18</b> दिउँसो <b>15:30:00</b> (03:30 PM)</td>
            </tr>
            <tr style="background-color: #241e1a;">
                <td><b>Dallas (Texas) / Chicago / Houston</b> (CDT)</td>
                <td>१० घण्टा ४५ मिनेट पछाडि</td>
                <td><b>2026-04-18</b> दिउँसो <b>14:30:00</b> (02:30 PM)</td>
            </tr>
            <tr>
                <td><b>Denver / Salt Lake City / Phoenix</b> (MDT)</td>
                <td>११ घण्टा ४५ मिनेट पछाडि</td>
                <td><b>2026-04-18</b> दिउँसो <b>13:30:00</b> (01:30 PM)</td>
            </tr>
            <tr style="background-color: #241e1a;">
                <td><b>Los Angeles / San Francisco / Seattle</b> (PDT)</td>
                <td>१२ घण्टा ४५ मिनेट पछाडि</td>
                <td><b>2026-04-18</b> दिउँसो <b>12:30:00</b> (12:30 PM)</td>
            </tr>
        </table>
        """
    },
    {
        "id": "location_selection",
        "title": "३. जन्मस्थान (सहर, देश, अक्षांश र देशान्तर) छनोट विधि",
        "keywords": "स्थान सहर देश जिल्ला अक्षांश देशान्तर latitude longitude timezone location city nepal india",
        "html": """
        <h2 style="color: #d4af37;">३. जन्मस्थान (Location) छनोट विधि</h2>
        <p style="font-size: 14px; line-height: 1.6;">
            शिवराम ज्योतिष सफ्टवेयरमा नेपालका सबै ७७ जिल्ला तथा प्रमुख नगरपालिकाहरू, भारतका सबै २८ राज्यहरू र विश्वका ६०० भन्दा बढी प्रमुख सहरहरूको पूर्ण भौगोलिक विवरण सुरक्षित छ।
        </p>

        <h3 style="color: #e5c158;">स्थान छान्ने तरिका:</h3>
        <ol style="line-height: 1.7; font-size: 14px;">
            <li><b>देश (Country) छान्नुहोस्:</b> नेपाल, India, USA, Canada, UK, Australia, UAE, Saudi Arabia, आदि।</li>
            <li><b>सहर (City / District) खोज्नुहोस्:</b> सहरको नाम टाइप गर्न सुरु गरेपछि तल सूची देखिन्छ, त्यसमा क्लिक गर्नुहोस्।</li>
            <li>सहर छान्ने बित्तिकै सफ्टवेयरले उक्त स्थानको <b>Latitude (अक्षांश), Longitude (देशान्तर) र Timezone (समय क्षेत्र)</b> स्वतः भरिदिन्छ।</li>
        </ol>

        <div style="background-color: #2b221b; border-left: 4px solid #58b9e5; padding: 12px; margin: 15px 0;">
            <b style="color: #79d2ff; font-size: 15px;">💡 यदि सानो गाउँ वा सूचीमा नभएको स्थान भएमा के गर्ने?</b>
            <p style="margin: 6px 0 0 0; line-height: 1.5;">
                तपाईंले कुनै पनि स्थानको <b>Latitude (उदा. 27.7172)</b> र <b>Longitude (उदा. 85.3240)</b> गुगल म्यापबाट हेरेर म्यानुअल्ली टाइप गर्न सक्नुहुन्छ। 
                सफ्टवेयरले विश्वको जुनसुकै स्थानको निर्देशांक अनुसार १००% सही स्थानीय सूर्योदय, इष्टकाल र लग्न गणना गर्दछ।
            </p>
        </div>
        """
    },
    {
        "id": "chart_navigation",
        "title": "४. कुण्डलीका मुख्य अङ्गहरू र हेर्ने तरिका (D1, D9, भाव चलित, अष्टकवर्ग)",
        "keywords": "कुण्डली लग्न नवांश भाव चलित अष्टकवर्ग षड्बल ग्रह स्थिति d1 d9 d10 cusp shashtiamsha",
        "html": """
        <h2 style="color: #d4af37;">४. कुण्डलीका मुख्य अङ्गहरू र हेर्ने तरिका</h2>
        <p style="font-size: 14px; line-height: 1.6;">
            कुण्डली गणना भइसकेपछि माथिका ट्याबहरू (Tabs) बाट विभिन्न खगोलीय तथा ज्योतिषीय विवरणहरू हेर्न सकिन्छ:
        </p>

        <ul style="line-height: 1.8; font-size: 14px;">
            <li><b>लग्न कुण्डली (D1 Rashi Chart):</b> जन्म लग्न, १२ वटा भावमा रहेका ग्रहहरू, राशि संख्या, वक्री/अस्त स्थिति।</li>
            <li><b>नवांश कुण्डली (D9 Navamsha Chart):</b> भाग्य, वैवाहिक जीवन र ग्रहहरूको आन्तरिक बल हेर्न।</li>
            <li><b>दशमांश (D10) र अन्य वर्ग कुण्डलीहरू:</b> D2 (होरा), D3 (द्रेष्काण), D4 (चतुर्थांश), D7 (सप्तांश), D10 (दशमांश - पेशा/व्यवसाय), D12 (द्वादशांश), D16 (षोडशांश), D20 (विंशांश), D24 (चतुर्विंशांश), D27 (सप्तविंशांश), D30 (त्रिंशांश), D60 (षष्ट्यंश)।</li>
            <li><b>भाव चलित तथा सन्धिसहित (Bhava Chalit & Cusp Sphutas):</b> कुन ग्रह कुन भावमा सरेको छ र भाव आरम्भ/मध्य/अन्त्य डिग्री कति छ।</li>
            <li><b>अवकहडा चक्र (Avakahada Chakra):</b> जन्म नामको पहिलो अक्षर, वर्ण, वश्य, तारा, योनि, गण, नाडी, चन्द्रराशि, नक्षत्र र पाउ।</li>
            <li><b>ग्रह स्पष्ट तालिका (Planetary Sphutas):</b> प्रत्येक ग्रहको शुद्ध डिग्री, कला, विकला, नक्षत्र, नक्षत्र स्वामी, उपस्वामी (Sub-lord)।</li>
            <li><b>षड्बल (Shadbala):</b> ६ प्रकारका ग्रह बल (स्थानबल, दिग्बल, कालबल, चेष्टाबल, नैसर्गिकल, दृग्बल) र कुन ग्रह कति रूप बलियो छ।</li>
            <li><b>अष्टकवर्ग (Ashtakavarga):</b> सर्वाष्टकवर्ग चक्र (SAV) र भिन्न-अष्टकवर्ग बिन्दुहरू।</li>
        </ul>
        """
    },
    {
        "id": "dasha_transit",
        "title": "५. विंशोत्तरी, योगिनी, चर दशा र गोचर विश्लेषण",
        "keywords": "दशा विंशोत्तरी योगिनी चर गोचर transit dasha antardasha pratyantardasha sadesati साढेसाती",
        "html": """
        <h2 style="color: #d4af37;">५. दशा र गोचर (Transit) विश्लेषण</h2>
        
        <h3 style="color: #e5c158;">१. विंशोत्तरी दशा (Vimshottari Dasha - १२० वर्ष चक्र):</h3>
        <p style="font-size: 14px; line-height: 1.6;">
            जन्म नक्षत्रका आधारमा भोग्य दशा निकाली महादशा, अन्तर्दशा, प्रत्यन्तर्दशा र सूक्ष्म दशासम्मको मिति तालिका देखाइन्छ। 
            सफ्टवेयरमा हाल चलिरहेको दशा स्वतः हरियो रङमा हाइलाइट हुन्छ।
        </p>

        <h3 style="color: #e5c158;">२. योगिनी दशा (Yogini Dasha - ३६ वर्ष चक्र):</h3>
        <p style="font-size: 14px; line-height: 1.6;">
            मंगला (१), पिंगला (२), धान्या (३), भ्रामरी (४), भद्रिका (५), उल्का (६), सिद्धा (७), संकटा (८) गरी आठवटा योगिनीहरूको दशा क्रम।
        </p>

        <h3 style="color: #e5c158;">३. जैमिनी चर दशा (Jaimini Chara Dasha):</h3>
        <p style="font-size: 14px; line-height: 1.6;">
            राशिहरूको आधारमा चल्ने चर दशा र आत्मकारक, अमात्यकारक, भ्रातृकारक आदि सात कारकहरूको निर्धारण।
        </p>

        <h3 style="color: #e5c158;">४. गोचर तथा साढेसाती (Gochara & Shani Sade Sati):</h3>
        <p style="font-size: 14px; line-height: 1.6;">
            वर्तमान समयमा आकाशमा घुमिरहेका ग्रहहरू जन्म कुण्डलीको चन्द्रमा र लग्नबाट कुन-कुन भावमा छन् र कस्तो फल दिन्छन्। 
            शनिको साढेसाती कुन चरण (प्रथम, द्वितीय, तृतीय) मा चलिरहेको छ र ढैया कहिले सुरु/समाप्त हुन्छ।
        </p>
        """
    },
    {
        "id": "panchanga_muhurta",
        "title": "६. दैनिक पञ्चाङ्ग, इष्टकाल र शुभ-अशुभ मुहूर्त",
        "keywords": "पञ्चाङ्ग मुहूर्त इष्टकाल सूर्योदय सूर्यास्त राहुकाल यमघण्ट अभिजित panchang muhurta ishtakala",
        "html": """
        <h2 style="color: #d4af37;">६. पञ्चाङ्ग, इष्टकाल र मुहूर्त</h2>
        
        <h3 style="color: #e5c158;">१. पञ्चाङ्गका ५ अङ्गहरू:</h3>
        <ul>
            <li><b>तिथि (Tithi):</b> सूर्य र चन्द्रमा बीचको १२° को अन्तर। समाप्ति समय सेकेन्डको शुद्धतामा।</li>
            <li><b>वार (Vara):</b> सूर्योदयदेखि अर्को सूर्योदयसम्मको दिन।</li>
            <li><b>नक्षत्र (Nakshatra):</b> चन्द्रमाले भोग गरिरहेको १३°२०' को क्षेत्र।</li>
            <li><b>योग (Yoga):</b> सूर्य र चन्द्रमाको देशान्तरको योगफल (२७ योग)।</li>
            <li><b>करण (Karana):</b> तिथिको आधा भाग (६°)।</li>
        </ul>

        <h3 style="color: #e5c158;">२. इष्टकाल (Ishtakala):</h3>
        <p style="font-size: 14px; line-height: 1.6;">
            <b>इष्टकाल = (जन्म समय - स्थानीय सूर्योदय समय) × २.५ घडी</b><br>
            हाम्रो इन्जिनले जन्मस्थानको शुद्ध स्थानीय सूर्योदय निकालेर इष्टकाल घडी र पलामा निकाल्छ।
        </p>

        <h3 style="color: #e5c158;">३. दैनिक शुभ र अशुभ मुहूर्तहरू:</h3>
        <ul>
            <li><b>राहुकाल (Rahu Kala):</b> दिनको १/८ भाग, कुनै पनि शुभ कार्य वर्जित।</li>
            <li><b>यमघण्ट / गुलिक काल:</b> अशुभ समय।</li>
            <li><b>अभिजित मुहूर्त (Abhijit Muhurta):</b> मध्याह्नको अत्यन्त शुभ मुहूर्त।</li>
            <li><b>दिनमान र रात्रिमान:</b> दिन र रातको कुल घडी/पला।</li>
        </ul>
        """
    },
    {
        "id": "matching_dosha",
        "title": "७. विवाह मेलापक तथा अष्टकूट मिलान (Matchmaking & Doshas)",
        "keywords": "विवाह मेलापक कुण्डली मिलान अष्टकूट भकूट नाडी गुण मिलान मंगली दोष matching manglik",
        "html": """
        <h2 style="color: #d4af37;">७. विवाह मेलापक तथा कुण्डली मिलान (Matchmaking)</h2>
        <p style="font-size: 14px; line-height: 1.6;">
            वर र कन्याको जन्म विवरण हालेपछि सफ्टवेयरले अष्टकूट मिलान (३६ गुण) र दोष परिहारको पूर्ण विश्लेषण निकाल्छ:
        </p>

        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; border-color: #44372c;">
            <tr style="background-color: #352a22; color: #d4af37;">
                <th>कूट (Koota)</th>
                <th>अधिकतम अंक</th>
                <th>के हेरिन्छ?</th>
            </tr>
            <tr><td>वर्ण (Varna)</td><td>१</td><td>अहंकार र सामाजिक स्वभाव</td></tr>
            <tr style="background-color: #241e1a;"><td>वश्य (Vashya)</td><td>२</td><td>पारस्परिक आकर्षण र नियन्त्रण</td></tr>
            <tr><td>तारा (Tara)</td><td>३</td><td>भाग्य, स्वास्थ्य र आयु</td></tr>
            <tr style="background-color: #241e1a;"><td>योनि (Yoni)</td><td>४</td><td>शारीरिक र मानसिक सामञ्जस्य</td></tr>
            <tr><td>ग्रहमैत्री (Graha Maitri)</td><td>५</td><td>मित्रता, दृष्टिकोण र समझदारी</td></tr>
            <tr style="background-color: #241e1a;"><td>गण (Gana)</td><td>६</td><td>व्यवहार र पारिवारिक स्वभाव</td></tr>
            <tr><td>भकूट (Bhakoot)</td><td>७</td><td>सन्तान, आर्थिक समृद्धि र दीर्घायु</td></tr>
            <tr style="background-color: #241e1a;"><td>नाडी (Nadi)</td><td>८</td><td>रक्त समूह, सन्तानोत्पत्ति र आनुवंशिकी</td></tr>
            <tr style="background-color: #352a22; color: #d4af37;"><td><b>कुल अंक</b></td><td><b>३६</b></td><td><b>१८ भन्दा माथि शुभ मानिन्छ</b></td></tr>
        </table>

        <h3 style="color: #e5c158; margin-top: 15px;">मङ्गल दोष (Mangal Dosha / Manglik):</h3>
        <p>लग्न, चतुर्थ, सप्तम, अष्टम वा द्वादश भावमा मङ्गल भएमा मङ्गल दोष मानिन्छ। सफ्टवेयरले दोष छ/छैन र दोष परिहार (Cancellation) भएको छ कि छैन, स्पष्ट खुलाउँछ।</p>
        """
    },
    {
        "id": "export_print",
        "title": "८. रिपोर्ट, प्रिन्ट र PDF एक्सपोर्ट (Printing & PDF Export)",
        "keywords": "पिडिएफ प्रिन्ट रिपोर्ट सेभ pdf print export report",
        "html": """
        <h2 style="color: #d4af37;">८. रिपोर्ट, प्रिन्ट र PDF एक्सपोर्ट</h2>
        <p style="font-size: 14px; line-height: 1.6;">
            तयार भएको कुण्डलीलाई ग्राहक वा आफ्नै प्रयोजनका लागि प्रिन्ट गर्न वा PDF मा सुरक्षित गर्न सकिन्छ:
        </p>

        <ol style="line-height: 1.8; font-size: 14px;">
            <li><b>PDF एक्सपोर्ट:</b> माथिल्लो मेनु वा बटनमा रहेको <b>📄 Export PDF</b> मा क्लिक गर्नुहोस्। सफ्टवेयरले आकर्षक नेपाली फन्ट र कुण्डली चक्रसहितको बहुपृष्ठीय रंगीन PDF फाइल सेभ गरिदिन्छ।</li>
            <li><b>सिधै प्रिन्ट (Direct Print):</b> <b>🖨️ Print Chart</b> बटनमा क्लिक गरेर A4 साइजमा सीधै प्रिन्टरबाट निकाल्न सकिन्छ।</li>
            <li><b>कुण्डली सेभ (Save Kundali):</b> नाम, ठेगाना र विवरण सुरक्षित राख्न <b>💾 Save</b> गर्नुहोस्, पछि <b>📁 Open Saved</b> बाट जुनसुकै बेला खोल्न सकिन्छ।</li>
        </ol>
        """
    },
    {
        "id": "faq_troubleshooting",
        "title": "९. बारम्बार सोधिने प्रश्नहरू (FAQs & Troubleshooting)",
        "keywords": "faq प्रश्न समस्या समाधान troubleshooting help error discrepancy",
        "html": """
        <h2 style="color: #d4af37;">९. बारम्बार सोधिने प्रश्नहरू (FAQs)</h2>

        <p><b>प्र. १: नेपाली पात्रोको नक्षत्र र कुण्डलीको नक्षत्र कहिलेकाहीँ किन फरक देखिन्छ?</b></p>
        <p style="color: #cfc5b8;">
            <b>उ:</b> नेपाली पात्रोमा लेखिएको नक्षत्र <i>"बिहान सूर्योदय हुँदाको नक्षत्र"</i> (Day's Nakshatra) हो। 
            चन्द्रमा दिनभरिमा करिब १३° हिँड्ने हुनाले दिउँसो वा राती जन्म हुँदा नक्षत्र अर्कोमा सरिसकेको हुन सक्छ। 
            व्यक्तिगत कुण्डलीले जातक जन्मिएको ठ्याक्कै त्यही सेकेन्डको चन्द्र स्थिति लिने भएकाले कुण्डलीको नक्षत्र १००% सही हुन्छ।
        </p>

        <p><b>प्र. २: कुन अयनांश (Ayanamsha) प्रयोग गर्नु राम्रो हुन्छ?</b></p>
        <p style="color: #cfc5b8;">
            <b>उ:</b> नेपाल र भारतको सरकारी तथा शास्त्रीय मान्यता प्राप्त <b>लाहिरी / चित्रपक्षीय अयनांश (Lahiri Ayanamsha)</b> सबैभन्दा भरपर्दो र मानक हो। सफ्टवेयरमा पूर्वनिर्धारित (Default) रूपमा यही चयन गरिएको हुन्छ।
        </p>

        <p><b>प्र. ३: के यो सफ्टवेयर इन्टरनेट बिना (Offline) चल्छ?</b></p>
        <p style="color: #cfc5b8;">
            <b>उ:</b> हो, सम्पूर्ण खगोलीय एफिमरिस (Swiss Ephemeris / JPL DE421) र ६००+ सहरहरूको डाटाबेस तपाईंको कम्प्युटरमै रहने भएकाले यो सफ्टवेयर इन्टरनेट नहुँदा पनि १००% अफलाइन चल्दछ।
        </p>
        """
    },
    {
        "id": "siddhantas",
        "title": "१०. पञ्चाङ्ग गणना सिद्धान्तहरू (दृक vs सूर्यसिद्धान्त vs ग्रहलाघव)",
        "keywords": "सिद्धान्त दृक सूर्यसिद्धान्त ग्रहलाघव केपी रमन siddhanta drik surya grahalaghava kp raman",
        "html": """
        <h2 style="color: #d4af37;">१०. पञ्चाङ्ग गणना सिद्धान्तहरू (Calculation Siddhantas)</h2>
        <p style="font-size: 14px; line-height: 1.6;">
            शिवराम ज्योतिष सफ्टवेयरमा प्रयोगकर्ताको आवश्यकता अनुसार फरक-फरक शास्त्रीय तथा खगोलीय सिद्धान्त छनोट गर्ने सुविधा उपलब्ध छ। 
            माथिल्लो मेनुको <b>विकल्प -> सेटिङ तथा प्राथमिकता</b> बाट वा कुण्डली फारमको <b>ज्योतिष सेटिंग</b> बाट सिद्धान्त छनोट गर्न सकिन्छ।
        </p>

        <h3 style="color: #e5c158;">उपलब्ध मुख्य सिद्धान्तहरू:</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; border-color: #44372c;">
            <tr style="background-color: #352a22; color: #d4af37;">
                <th>गणना सिद्धान्त</th>
                <th>आधार र प्रविधि</th>
                <th>विशेष उपयोगिता</th>
            </tr>
            <tr>
                <td><b>१. दृक-सिद्धान्त (Drik - Swiss Ephemeris) [पूर्वनिर्धारित]</b></td>
                <td>नासा (NASA JPL DE421) तथा आधुनिक टेलिस्कोपिक शुद्ध खगोल गणित।</td>
                <td><b>व्यक्तिगत कुण्डली (Horoscope), जन्मलग्न, ग्रहस्पष्ट र दशाका लागि संसारकै सबैभन्दा प्रमाणित र शुद्ध।</b></td>
            </tr>
            <tr style="background-color: #241e1a;">
                <td><b>२. सूर्यसिद्धान्त (Surya Siddhanta)</b></td>
                <td>प्राचीन मन्दकेन्द्र/शीघ्रकेन्द्र सारिणी तथा नेपाल पञ्चाङ्ग निर्णायक विकास समिति मोडेल।</td>
                <td>नेपाली छापिएका परम्परागत पात्रोहरूको समयसँग हुबहु तालिका हेर्न।</td>
            </tr>
            <tr>
                <td><b>३. ग्रहलाघव पद्धति (Grahalaghava System)</b></td>
                <td>गणेश दैवज्ञ कृत ग्रहलाघव / आर्यभटीय परम्परागत मध्यम गति गणित।</td>
                <td>परम्परागत पञ्चाङ्ग गणितीय तुलनाका लागि।</td>
            </tr>
            <tr style="background-color: #241e1a;">
                <td><b>४. कृष्णमूर्ति पद्धति (KP System)</b></td>
                <td>केपी अयनांश तथा प्लेसिडस (Placidus) भाव चलित उपस्वामी (Sub-lord) गणित।</td>
                <td>केपी ज्योतिष तथा प्रश्न कुण्डली विश्लेषणका लागि।</td>
            </tr>
            <tr>
                <td><b>५. बि.भि. रमन पद्धति (BV Raman System)</b></td>
                <td>डा. बि.भि. रमन अयनांश र समान भाव पद्धति।</td>
                <td>रमन ज्योतिष परम्पराका शोधकर्ताहरूका लागि।</td>
            </tr>
        </table>

        <div style="background-color: #2b221b; border-left: 4px solid #d4af37; padding: 12px; margin: 15px 0;">
            <b style="color: #e5c158; font-size: 15px;">💡 स्थायी रूपमा सुरक्षित हुने नियम:</b>
            <p style="margin: 6px 0 0 0; line-height: 1.5;">
                सेटिङमा गएर एकपटक सिद्धान्त परिवर्तन गरी <b>सुरक्षित (Save)</b> गरेपछि, तपाईंले पुनः नबदलिएसम्म सफ्टवेयरले सधैं सोही सिद्धान्त अनुसार कुण्डली र पञ्चाङ्ग गणना गर्दछ।
            </p>
        </div>
        """
    }
]


PAGE_GUIDE_TOPICS = [
    {
        "id": "page_bhava_chalit",
        "title": "यो पेज कसरी हेर्ने? (भाव चलित निर्देशिका)",
        "keywords": "भाव चलित chalit श्रीपति shripati भाव मध्य सन्धि ग्रह विस्थापन shift पराशरी",
        "html": """
        <h2 style="color: #d4af37;">भाव चलित निर्देशिका (Bhava Chalit)</h2>
        <ol style="line-height: 1.8; font-size: 14px;">
            <li><b>श्रीपति भाव चलित (Shripati Bhava Chalit):</b> जन्म लग्नका आधारमा भावको प्रारम्भ, मध्य र सन्धि विन्दु गणना गरी वास्तविक ग्रहको भाव स्थिति निर्धारण गरिन्छ।</li>
            <li><b>ग्रह विस्थापन (Planet Shift):</b> जन्म कुण्डली (D1) मा बसेको राशि र भाव चलितमा ग्रह बसेको भाव फरक हुन सक्छ। ग्रहले आफ्नो वास्तविक फल भाव चलितको भाव अनुसार दिन्छ।</li>
            <li><b>भाव सन्धि र मध्य:</b> भाव मध्यको नजिक रहेका ग्रहहरूले १००% पूर्ण फल दिन्छन् भने सन्धिको नजिक रहेका ग्रहहरूको प्रभाव कमजोर हुन्छ।</li>
        </ol>
        """
    },
    {
        "id": "page_panchang_view",
        "title": "यो पेज कसरी हेर्ने? (दैनिक पञ्चाङ्ग निर्देशिका)",
        "keywords": "पञ्चाङ्ग panchang तिथि वार नक्षत्र योग करण संकल्प सूर्योदय स्पष्टग्रह क्यालेन्डर",
        "html": """
        <h2 style="color: #d4af37;">दैनिक पञ्चाङ्ग निर्देशिका</h2>
        <ol style="line-height: 1.8; font-size: 14px;">
            <li><b>इन्टरएक्टिभ क्यालेन्डर:</b> क्यालेन्डरबाट कुनै पनि वर्ष, महिना वा गते क्लिक गरेर सो दिनको तत्काल विस्तृत पञ्चाङ्ग गणना गर्न सकिन्छ। 'आजको पञ्चाङ्ग' बटनले हालको दिन चयन गर्दछ।</li>
            <li><b>पञ्चाङ्गका पाँच अङ्ग:</b> तिथि, वार, नक्षत्र, योग र करणको सुरु र समाप्ति समय स्पष्ट रूपमा देखाइएको छ।</li>
            <li><b>दैनिक संकल्प श्लोक:</b> पूजा, पाठ, अनुष्ठान वा श्राद्धमा उच्चारण गरिने शास्त्रसम्मत पूर्ण संकल्प मन्त्र (स्थान, संवत्सर, ऋतु, अयन, तिथि, वार सहित) स्वचालित तयार हुन्छ।</li>
            <li><b>सूर्योदयकालीन स्पष्टग्रह:</b> सो दिन बिहान सूर्योदयको समयमा ९ वटा ग्रहहरू कुन राशि र अंशमा छन् भन्ने जानकारी प्रदान गर्दछ।</li>
        </ol>
        """
    },
    {
        "id": "page_sadesati_view",
        "title": "यो पेज कसरी हेर्ने? (साढेसाती निर्देशिका)",
        "keywords": "साढेसाती sadesati अढैया ढैया शनि चन्द्र राशि प्रथम द्वितीय तृतीय चरण फलादेश",
        "html": """
        <h2 style="color: #d4af37;">साढेसाती तथा अढैया निर्देशिका</h2>
        <ol style="line-height: 1.8; font-size: 14px;">
            <li><b>साढेसाती कालखण्ड (7.5 Year Period):</b> शनिग्रहले जन्म चन्द्र राशिको अगिल्लो राशि (१२ औं), चन्द्र राशि र पछिल्लो राशिमा गोचर गर्दा कुल ७.५ वर्षको साढेसाती सुरु हुन्छ।</li>
            <li><b>तीन खण्ड (3 Phases):</b> पहिलो खण्ड (ढैया) — रोग/कार्यस्थल परिवर्तन; मध्य खण्ड — आर्थिक र सामाजिक दबाब; तेस्रो खण्ड — विवाह/गृहस्थ सम्बन्धमा दबाब।</li>
            <li><b>शनिको ढैया (2.5 Year Dhayya):</b> शनिले जन्म चन्द्र राशिभन्दा चौथो वा आठौं राशिमा गोचर गर्दा ढैया (२.५ वर्ष) बन्छ।</li>
            <li><b>फलादेश नियम:</b> साढेसाती वा ढैयाको समयमा कठोर परिश्रम, शनिको आराधना, काला तिल दान र महामृत्युञ्जय जप गर्नाले कष्ट कम हुन्छ। जन्म कुण्डलीमा शनि बलवान् भएमा साढेसाती पनि शुभ फल दिन्छ।</li>
        </ol>
        """
    },
    {
        "id": "page_visual_graphs_view",
        "title": "यो पेज कसरी हेर्ने? (भिजुअल ग्राफ निर्देशिका)",
        "keywords": "भिजुअल ग्राफ visual graph ग्रह बल shadbala भाव शक्ति दशा टाइमलाइन बार चार्ट",
        "html": """
        <h2 style="color: #d4af37;">भिजुअल ग्राफ निर्देशिका</h2>
        <ol style="line-height: 1.8; font-size: 14px;">
            <li><b>ग्रह बल ग्राफ (Planet Strength Graph):</b> प्रत्येक ग्रहको सापेक्षिक बल (Shadbala वा समग्र शक्ति) बार ग्राफमा देखाइन्छ। लामो बार = बलवान् ग्रह = सो ग्रहको दशा/गोचर अत्यन्त शुभ हुन्छ।</li>
            <li><b>भाव शक्ति ग्राफ (House Strength):</b> कुण्डलीका १२ भावहरूको बल देखाइन्छ। बलवान् भावबाट सो भावसम्बन्धी (जस्तै: ७औं = विवाह, १०औं = करियर) विषयमा राम्रो फल मिल्छ।</li>
            <li><b>दशा टाइमलाइन (Dasha Timeline):</b> जीवनको दशाक्रम समयरेखामा देखाइन्छ। कुन उमेरमा कुन दशा आउँछ र कति अवधिसम्म रहन्छ सहजै बुझ्न सकिन्छ।</li>
            <li><b>ग्राफ विश्लेषण नियम:</b> जुन ग्रहको बार सबैभन्दा अग्लो छ र सो ग्रह त्रिकोण-केन्द्रमा राम्रो छ भने त्यसको दशामा जीवनको सर्वोत्तम समय आउँछ।</li>
        </ol>
        """
    },
    {
        "id": "page_varga_view",
        "title": "यो पेज कसरी हेर्ने? (वर्ग कुण्डली निर्देशिका)",
        "keywords": "वर्ग कुण्डली varga divisional D1 D9 D10 विभाजन लग्न ग्रह स्थिति फलादेश",
        "html": """
        <h2 style="color: #d4af37;">वर्ग कुण्डली निर्देशिका</h2>
        <ol style="line-height: 1.8; font-size: 14px;">
            <li><b>वर्ग कुण्डली समूह (Divisional Charts):</b> ड्रपडाउनबाट D1 (राशि) देखि D60 (षष्ट्यांश) सम्मका १६ वटा वर्ग कुण्डलीहरू चयन गरी हेर्न सकिन्छ।</li>
            <li><b>वर्ग विश्लेषण प्यानल (Right Panel):</b> दायाँतर्फ चयनित वर्ग कुण्डलीको लग्न, ग्रहहरूको स्थिति (उच्च, नीच, स्वगृही, मित्र/शत्रु राशि) र विशेष फलादेश तालिकामा देखिन्छ।</li>
            <li><b>वर्ग कुण्डली हेर्ने नियम:</b> जीवनको विशेष पक्ष विश्लेषण गर्दा सम्बन्धित वर्ग कुण्डली (जस्तै: D9 विवाह, D10 करियर, D7 सन्तान) को लग्न, लग्नेश र कारक ग्रहको शुभ/अशुभ स्थिति जाँच्नुपर्छ।</li>
        </ol>
        """
    },
    {
        "id": "page_sudarshan_view",
        "title": "यो पेज कसरी हेर्ने? (सुदर्शन चक्र निर्देशिका)",
        "keywords": "सुदर्शन चक्र sudarshan chakra लग्न चन्द्र सूर्य तीन वृत्त त्रि-दृष्टि BPHS",
        "html": """
        <h2 style="color: #d4af37;">सुदर्शन चक्र निर्देशिका</h2>
        <ol style="line-height: 1.8; font-size: 14px;">
            <li><b>सुदर्शन चक्र (BPHS Ch. 74):</b> तीन वटा केन्द्रिय वृत्तहरू — भित्री (लग्न कुण्डली - शरीर/भौतिक), मध्य (चन्द्र कुण्डली - मन/भावना) र बाहिरी (सूर्य कुण्डली - आत्मा/प्रतिष्ठा) बाट एउटै ग्रहस्थितिको त्रि-दृष्टिकोण तुलना गरिन्छ।</li>
            <li><b>भावगत त्रि-दृष्टि नियम:</b> यदि कुनै भाव तीनै चक्र (लग्न, चन्द्र, सूर्य) बाट शुभ ग्रहयुक्त वा शुभ दृष्टियुक्त छ भने सो भावसम्बन्धी जीवनको क्षेत्रमा १००% सफलता र कीर्ति मिल्छ।</li>
            <li><b>अशुभ प्रभाव:</b> तीनै स्थानबाट पाप प्रभाव परेमा सो क्षेत्रमा विशेष सतर्कता र उपाय गर्नुपर्छ।</li>
        </ol>
        """
    },
    {
        "id": "page_dasha_gochar_view",
        "title": "यो पेज कसरी हेर्ने? (दशा-गोचर निर्देशिका)",
        "keywords": "दशा गोचर dasha gochar मासिक चार्ट समय रेखा timeline गते क्लिक विश्लेषण",
        "html": """
        <h2 style="color: #d4af37;">दशा-गोचर चार्ट निर्देशिका</h2>
        <ol style="line-height: 1.8; font-size: 14px;">
            <li><b>गतेमा क्लिक गर्दा रेखा सर्ने:</b> बायाँ वा दायाँ कुनै पनि गतेमा क्लिक गर्दा चयन रेखा (Marker Line) सोही दिनमा सर्दछ र दशा विवरण तत्काल अपडेट हुन्छ।</li>
            <li><b>दुईवटा भ्यू मोड (View Modes):</b><br>
                • <b>📅 मासिक चार्ट (Grid):</b> प्रत्येक दिन कुन ग्रह कुन राशिमा कति डिग्रीमा छ, कोठाभित्र स्पष्ट देखिन्छ।<br>
                • <b>📈 समय रेखा (Timeline):</b> ९ वटै ग्रहहरूको दैनिक गति निरन्तर रङ्गीन रेखाका रूपमा देखिन्छ।</li>
            <li><b>फलादेश नियम:</b> बायाँ खण्डमा देखिएका दशानाथ ग्रहहरूको दायाँ खण्डमा गोचर अवस्था (लग्न/चन्द्र राशिबाट कतिऔं भावमा छन्) दाँजेर सो दिनको कार्यसिद्धि र शुभ-अशुभ सम्भावना निर्धारण गर्नुहोस्।</li>
        </ol>
        """
    },
    {
        "id": "page_prashna_view",
        "title": "यो पेज कसरी चलाउने? (प्रश्न कुण्डली निर्देशिका)",
        "keywords": "प्रश्न कुण्डली prashna horary खोज search विषय अवस्था फलादेश",
        "html": """
        <h2 style="color: #d4af37;">प्रश्न कुण्डली निर्देशिका</h2>
        <ol style="line-height: 1.8; font-size: 14px;">
            <li><b>प्रश्न खोज्नुहोस्:</b> माथिल्लो सर्च बक्समा कुनै पनि शब्द (जस्तै: <i>कति सन्तान, कुन जागिर, विवाह मिति, सन्तान, परीक्षा, धन</i>) टाइप गर्दा सो सम्बन्धी सम्पूर्ण प्रश्नहरूको सूची तुरुन्त देखिन्छ, जसमा क्लिक गरी सिधै उत्तर पाउन सक्नुहुन्छ।</li>
            <li><b>विषय र प्रश्न छान्नुहोस्:</b> १८ वटा प्रमुख जीवन क्षेत्रहरूमध्ये आफूलाई चाहिएको विषय र विशिष्ट प्रश्न चयन गर्न सक्नुहुन्छ।</li>
            <li><b>डिफल्ट सामान्य विश्लेषण:</b> कुनै अवस्था छनोट नगरी सिधै कुण्डलीको शुद्ध ज्योतिषीय नियम अनुसार फल प्राप्त हुन्छ। यदि जातकको अवस्था स्पष्ट खुलाउन चाहेमा मात्र माथिको सन्दर्भ अप्सन छनोट गर्न सक्नुहुन्छ।</li>
        </ol>
        """
    },
]


class UserGuideDialog(QDialog):
    """Rich searchable user guide dialog in Nepali."""

    def __init__(self, parent: Optional[QWidget] = None, initial_topic: Optional[str] = None):
        super().__init__(parent)
        self.setWindowTitle("📖 प्रयोगकर्ता निर्देशिका तथा कुण्डली इनपुट गाइड (User Guide)")
        self.resize(980, 680)
        self.setMinimumSize(800, 500)
        self._init_ui()
        if initial_topic:
            self._select_topic_by_id(initial_topic)
        else:
            self._topic_list.setCurrentRow(0)
            self._on_topic_selected(0)

    def _init_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG_DARK};
                color: {TEXT_PRIMARY};
            }}
            QLabel {{
                color: {TEXT_PRIMARY};
            }}
            QLineEdit {{
                background-color: {BG_CARD};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLOR_GOLD};
            }}
            QListWidget {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                color: {TEXT_PRIMARY};
                padding: 4px;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 10px 8px;
                border-bottom: 1px solid #2e2620;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: #3d2a1e;
                color: {COLOR_GOLD};
                font-weight: bold;
                border-left: 4px solid {COLOR_GOLD};
            }}
            QListWidget::item:hover:!selected {{
                background-color: #2b221b;
            }}
            QTextBrowser {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                color: {TEXT_PRIMARY};
                padding: 18px;
                font-family: 'Segoe UI', 'Mukta', 'Kalimati', sans-serif;
            }}
            QPushButton {{
                background-color: {COLOR_PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #a32412;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header Bar
        header_layout = QHBoxLayout()
        header_icon = QLabel("📖")
        header_icon.setStyleSheet("font-size: 24px;")
        header_title = QLabel("शिवराम ज्योतिष: प्रयोगकर्ता निर्देशिका तथा कुण्डली इनपुट गाइड")
        header_title.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {COLOR_GOLD};")
        header_layout.addWidget(header_icon)
        header_layout.addWidget(header_title)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # Search Bar
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 खोज्नुहोस् (Search):")
        search_label.setStyleSheet(f"font-size: 13px; color: {TEXT_MUTED}; font-weight: bold;")
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("कुनै पनि विषय वा शब्द खोज्नुहोस् (जस्तै: अमेरिका, राती १ बजे, दशा, लग्न, इष्टकाल, DST, अष्टकवर्ग)...")
        self._search_input.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self._search_input, 1)

        main_layout.addLayout(search_layout)

        # Splitter: Left Topic List, Right Content Browser
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(8)

        # Left List
        self._topic_list = QListWidget()
        self._populate_topic_list()
        self._topic_list.currentRowChanged.connect(self._on_topic_selected)
        splitter.addWidget(self._topic_list)

        # Right Content
        self._content_browser = QTextBrowser()
        self._content_browser.setOpenExternalLinks(True)
        splitter.addWidget(self._content_browser)

        splitter.setSizes([320, 660])
        main_layout.addWidget(splitter, 1)

        # Bottom Bar with Close Button
        bottom_layout = QHBoxLayout()
        hint_label = QLabel("💡 सुझाव: किबोर्डमा 'Esc' थिचेर वा 'बन्द गर्नुहोस्' बटन थिचेर बाहिरिन सक्नुहुन्छ।")
        hint_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        bottom_layout.addWidget(hint_label)
        bottom_layout.addStretch()

        close_btn = QPushButton("बन्द गर्नुहोस् (Close)")
        close_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(close_btn)

        main_layout.addLayout(bottom_layout)

    def _populate_topic_list(self, filter_text: str = ""):
        self._topic_list.clear()
        filter_clean = filter_text.strip().casefold()

        for topic in GUIDE_TOPICS:
            if not filter_clean or (
                filter_clean in topic["title"].casefold()
                or filter_clean in topic["keywords"].casefold()
                or filter_clean in topic["html"].casefold()
            ):
                item = QListWidgetItem(topic["title"])
                item.setData(Qt.UserRole, topic)
                self._topic_list.addItem(item)

        if self._topic_list.count() > 0:
            self._topic_list.setCurrentRow(0)
        else:
            self._content_browser.setHtml(
                f"<div style='text-align: center; padding: 50px; color: {TEXT_MUTED};'>"
                "<h3>कुनै पनि नतिजा फेला परेन।</h3>"
                "<p>कृपया फरक शब्द प्रयोग गरी पुनः खोज्नुहोस्।</p></div>"
            )

    def _on_search_text_changed(self, text: str):
        self._populate_topic_list(text)

    def _on_topic_selected(self, row: int):
        if row < 0:
            return
        item = self._topic_list.item(row)
        if not item:
            return
        topic = item.data(Qt.UserRole)
        if topic and "html" in topic:
            self._content_browser.setHtml(topic["html"])

    def _select_topic_by_id(self, topic_id: str):
        for i in range(self._topic_list.count()):
            item = self._topic_list.item(i)
            topic = item.data(Qt.UserRole)
            if topic and topic.get("id") == topic_id:
                self._topic_list.setCurrentRow(i)
                break


def show_user_guide(parent: Optional[QWidget] = None, initial_topic: Optional[str] = None):
    """Helper function to show the User Guide dialog."""
    dlg = UserGuideDialog(parent, initial_topic=initial_topic)
    dlg.exec()


def show_page_guide(parent: Optional[QWidget] = None, topic_id: Optional[str] = None):
    """Open the User Guide dialog focused on a page-specific topic.

    The dialog merges the global guide topics with the per-page guide topics, so
    when a page's bottom "निर्देशिका" button is clicked the matching per-page
    option appears in the topic list already selected (highlighted). Because the
    guide opens in its own window, the underlying page content is never covered.
    """
    # Page-specific topics are listed first so the clicked page stands out.
    merged = PAGE_GUIDE_TOPICS + GUIDE_TOPICS
    original = UserGuideDialog._populate_topic_list

    def _populate_with_pages(self, filter_text: str = ""):
        self._topic_list.clear()
        filter_clean = filter_text.strip().casefold()
        for topic in merged:
            if not filter_clean or (
                filter_clean in topic["title"].casefold()
                or filter_clean in topic["keywords"].casefold()
                or filter_clean in topic["html"].casefold()
            ):
                item = QListWidgetItem(topic["title"])
                item.setData(Qt.UserRole, topic)
                self._topic_list.addItem(item)

        if self._topic_list.count() > 0:
            self._topic_list.setCurrentRow(0)
        else:
            self._content_browser.setHtml(
                f"<div style='text-align: center; padding: 50px; color: {TEXT_MUTED};'>"
                "<h3>कुनै पनि नतिजा फेला परेन।</h3>"
                "<p>कृपया फरक शब्द प्रयोग गरी पुनः खोज्नुहोस्।</p></div>"
            )

    UserGuideDialog._populate_topic_list = _populate_with_pages
    try:
        dlg = UserGuideDialog(parent)
        if topic_id:
            dlg._select_topic_by_id(topic_id)
        dlg.exec()
    finally:
        UserGuideDialog._populate_topic_list = original
