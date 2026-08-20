"""
Comprehensive Test Call Scenarios for Question 3 (2 Calls per Market = 4 Calls Total)
Includes authentic dialogues, diarized turns, code-switching analysis, and localization evidence.
"""

from typing import List, Dict
from backend.app.q3_multilingual_bots.models import (
    MarketCode,
    ScenarioRecord,
    DialogueTurn,
    DialogueRole,
)

Q3_SCENARIOS: List[ScenarioRecord] = [
    # -------------------------------------------------------------------------
    # PHILIPPINES SCENARIO 1: Cooperative Taglish Bancassurance Renewal
    # -------------------------------------------------------------------------
    ScenarioRecord(
        scenario_id="ph_cooperative_renewal",
        market_code=MarketCode.PHILIPPINES,
        title="🇵🇭 PH Call 1: Cooperative Taglish Bancassurance Renewal & Rider Cross-Sell",
        description="Client receives a renewal reminder for their BDO bancassurance life policy and inquires about adding a Hospital Income Benefit rider in natural Taglish.",
        test_category="cooperative",
        expected_outcome="Successfully handles premium verification, explains rider benefits in Taglish, and sets auto-debit confirmation.",
        adaptation_highlights=[
            "Seamless mixing of Tagalog and English loanwords ('policy', 'beneficiary', 'rider', 'auto-debit').",
            "Polite Filipino customer service particles ('po', 'opo', 'ma'am').",
            "Culturally familiar bancassurance bank-partner references (BDO / BPI)."
        ],
        timeline=[
            DialogueTurn(
                role=DialogueRole.AGENT,
                speaker_name="Maria (Agent)",
                text="Magandang araw po Ma'am! Ako po si Maria mula sa Darwix Bancassurance. Tumatawag po ako para mag-follow up sa inyong life policy review na magdu-due po ngayong 25th.",
                audio_timestamp_start=0.0,
                audio_timestamp_end=6.2,
                cultural_markers=["po", "Magandang araw", "magdu-due"]
            ),
            DialogueTurn(
                role=DialogueRole.CUSTOMER,
                speaker_name="Carla (Customer)",
                text="Hello Maria! Oo nga pala, received ko yung text reminder niyo. Magkano po ba ulit yung annual premium ko? Saka ask ko lang kung pwede ko bang isama yung anak ko as secondary beneficiary?",
                audio_timestamp_start=6.5,
                audio_timestamp_end=14.0,
                cultural_markers=["po", "Oo nga pala", "annual premium", "beneficiary"]
            ),
            DialogueTurn(
                role=DialogueRole.AGENT,
                speaker_name="Maria (Agent)",
                text="Opo Ma'am Carla. Ang annual premium po ninyo ay ₱24,000 for a ₱1.5 Million life coverage. Yes po, pwede pong-pwede nating i-add ang inyong anak as secondary beneficiary online gamit lang ang kanyang birth certificate.",
                audio_timestamp_start=14.5,
                audio_timestamp_end=24.0,
                cultural_markers=["Opo", "pwede pong-pwede", "life coverage"]
            ),
            DialogueTurn(
                role=DialogueRole.CUSTOMER,
                speaker_name="Carla (Customer)",
                text="Ayos! May promo po ba kayo ngayon para sa health o medical riders? Baka pwedeng i-upgrade yung coverage ko.",
                audio_timestamp_start=24.5,
                audio_timestamp_end=30.0,
                cultural_markers=["Ayos", "riders", "coverage"]
            ),
            DialogueTurn(
                role=DialogueRole.AGENT,
                speaker_name="Maria (Agent)",
                text="Tamang-tama po Ma'am! May Hospital Income Benefit rider po tayo na ₱2,500 daily allowance kapag na-confine sa ospital, dagdag lang po ng ₱350 per month. Gusto niyo po bang i-attach natin ito sa inyong auto-debit arrangement?",
                audio_timestamp_start=30.5,
                audio_timestamp_end=41.0,
                cultural_markers=["Tamang-tama po", "Hospital Income Benefit", "auto-debit arrangement"]
            ),
            DialogueTurn(
                role=DialogueRole.CUSTOMER,
                speaker_name="Carla (Customer)",
                text="Sige po Maria, paki-dagdag na po yan. I-confirm ko na lang sa link na ipapadala niyo. Salamat po!",
                audio_timestamp_start=41.5,
                audio_timestamp_end=47.0,
                cultural_markers=["Sige po", "Salamat po"]
            ),
        ]
    ),

    # -------------------------------------------------------------------------
    # PHILIPPINES SCENARIO 2: Taglish Hardship Objection & Lapse Grace Period
    # -------------------------------------------------------------------------
    ScenarioRecord(
        scenario_id="ph_hardship_lapse_objection",
        market_code=MarketCode.PHILIPPINES,
        title="🇵🇭 PH Call 2: Taglish Financial Hardship, Lapse Grace Period & In-Language Fallback",
        description="Customer has budget constraints ('gipit'), worries about immediate policy lapse, and asks about payment restructuring.",
        test_category="objection",
        expected_outcome="Reassures customer with empathy in Taglish, explains 31-day grace period, and converts annual mode to quarterly.",
        adaptation_highlights=[
            "Handling Filipino colloquial expression of financial distress ('medyo gipit ngayon').",
            "Accurate explanation of statutory 31-day grace period under Philippine Insurance Commission rules.",
            "Reassures family protection value without aggressive hard-selling."
        ],
        timeline=[
            DialogueTurn(
                role=DialogueRole.AGENT,
                speaker_name="Maria (Agent)",
                text="Hello Sir Jonathan, magandang hapon po. Paalala lang po sana mula sa Darwix Bancassurance hinggil sa inyong quarterly premium na mag-expire po sa Friday.",
                audio_timestamp_start=0.0,
                audio_timestamp_end=7.0,
                cultural_markers=["po", "magandang hapon", "quarterly premium"]
            ),
            DialogueTurn(
                role=DialogueRole.CUSTOMER,
                speaker_name="Jonathan (Customer)",
                text="Naku Maria, pasensya na. Medyo gipit po kasi ang budget ko ngayon dahil sa tuition fee ng mga bata. Baka kailangan ko munang i-cancel o mag-la-lapse ba agad yung policy ko?",
                audio_timestamp_start=7.5,
                audio_timestamp_end=16.5,
                cultural_markers=["Naku", "pasensya na", "gipit", "mag-la-lapse"]
            ),
            DialogueTurn(
                role=DialogueRole.AGENT,
                speaker_name="Maria (Agent)",
                text="Naiintindihan ko po kayo, Sir Jonathan. Priority po talaga ang pamilya. Huwag po kayong mag-alala, may statutory 31-day grace period po tayo mula sa due date bago mag-lapse ang policy, kaya fully insured pa rin po kayo ngayong buwan.",
                audio_timestamp_start=17.0,
                audio_timestamp_end=28.5,
                cultural_markers=["Naiintindihan ko po", "31-day grace period", "fully insured"]
            ),
            DialogueTurn(
                role=DialogueRole.CUSTOMER,
                speaker_name="Jonathan (Customer)",
                text="Ah ganun ba? Akala ko ma-fo-forfeit agad. Pero paano kung hindi pa rin kaya sa katapusan? Pwede bang quarterly to monthly muna?",
                audio_timestamp_start=29.0,
                audio_timestamp_end=36.5,
                cultural_markers=["Ah ganun ba", "ma-fo-forfeit", "quarterly to monthly"]
            ),
            DialogueTurn(
                role=DialogueRole.AGENT,
                speaker_name="Maria (Agent)",
                text="Opo Sir, pwedeng-pwede po! Pwede po nating i-convert sa monthly payment mode na ₱1,800 lang per month para mas magaan sa inyong monthly cash flow. I-schedule po ba natin ang payment sa susunod na sahod po ninyo?",
                audio_timestamp_start=37.0,
                audio_timestamp_end=48.0,
                cultural_markers=["Opo", "pwedeng-pwede", "sahod"]
            ),
            DialogueTurn(
                role=DialogueRole.CUSTOMER,
                speaker_name="Jonathan (Customer)",
                text="Napakalaking tulong po niyan Maria. Sige po, i-set po natin sa 15th pagka-sahod. Maraming salamat sa tulong po.",
                audio_timestamp_start=48.5,
                audio_timestamp_end=55.0,
                cultural_markers=["Napakalaking tulong", "Maraming salamat"]
            ),
        ]
    ),

    # -------------------------------------------------------------------------
    # INDONESIA SCENARIO 1: Cooperative Bahasa Multifinance Installment
    # -------------------------------------------------------------------------
    ScenarioRecord(
        scenario_id="id_cooperative_installment",
        market_code=MarketCode.INDONESIA,
        title="🇮🇩 ID Call 1: Cooperative Bahasa Multifinance Installment & Tenor Follow-Up",
        description="Customer confirms vehicle financing installment payment, checks remaining tenor, and asks about early payoff discount.",
        test_category="cooperative",
        expected_outcome="Politely verifies contract number, provides exact angsuran amount & remaining tenor, and explains pelunasan dipercepat rules.",
        adaptation_highlights=[
            "Natural formal and colloquial banking tone ('Bapak', 'cicilan', 'jatuh tempo', 'tenor', 'pelunasan dipercepat').",
            "Respectful Indonesian opening and closing honorifics.",
            "Accurate Rupiah currency figures and OJK-compliant fee explanations."
        ],
        timeline=[
            DialogueTurn(
                role=DialogueRole.AGENT,
                speaker_name="Dewi (Agent)",
                text="Selamat pagi Bapak Hendra, saya Dewi dari Darwix Multifinance. Semoga Bapak dalam keadaan sehat. Kami ingin mengonfirmasi jadwal angsuran pembiayaan mobil Bapak yang jatuh tempo tanggal 22 nanti ya Pak.",
                audio_timestamp_start=0.0,
                audio_timestamp_end=8.5,
                cultural_markers=["Selamat pagi", "Bapak", "angsuran", "jatuh tempo"]
            ),
            DialogueTurn(
                role=DialogueRole.CUSTOMER,
                speaker_name="Hendra (Customer)",
                text="Halo Bu Dewi, iya betul. Kemarin saya sudah transfer via Virtual Account BCA sebesar Rp 4.250.000. Apakah sudah terverifikasi di sistem?",
                audio_timestamp_start=9.0,
                audio_timestamp_end=17.5,
                cultural_markers=["Bu Dewi", "Virtual Account", "Rp 4.250.000"]
            ),
            DialogueTurn(
                role=DialogueRole.AGENT,
                speaker_name="Dewi (Agent)",
                text="Baik Bapak Hendra, kami cek pembayaran angsuran ke-14 sudah sukses terverifikasi lunas. Sisa tenor pembiayaan Bapak tinggal 22 bulan lagi ya Pak.",
                audio_timestamp_start=18.0,
                audio_timestamp_end=27.0,
                cultural_markers=["Baik Bapak", "terverifikasi lunas", "sisa tenor"]
            ),
            DialogueTurn(
                role=DialogueRole.CUSTOMER,
                speaker_name="Hendra (Customer)",
                text="Alhamdulillah, terima kasih Bu. Kalau semisal bulan depan saya mau pelunasan dipercepat ada potongan bunga nggak ya?",
                audio_timestamp_start=27.5,
                audio_timestamp_end=34.5,
                cultural_markers=["Alhamdulillah", "pelunasan dipercepat", "potongan bunga"]
            ),
            DialogueTurn(
                role=DialogueRole.AGENT,
                speaker_name="Dewi (Agent)",
                text="Tentu ada keringanan bunga Bapak Hendra. Untuk pelunasan dipercepat, bunga sisa tenor akan dipotong dan hanya dikenakan biaya administrasi 2% dari sisa pokok. Nanti kami kirimkan rincian simulasinya via WhatsApp resmi kami ya Pak.",
                audio_timestamp_start=35.0,
                audio_timestamp_end=47.5,
                cultural_markers=["keringanan bunga", "sisa pokok", "simulasi via WhatsApp"]
            ),
            DialogueTurn(
                role=DialogueRole.CUSTOMER,
                speaker_name="Hendra (Customer)",
                text="Bagus kalau begitu Bu Dewi, sangat membantu. Terima kasih banyak ya.",
                audio_timestamp_start=48.0,
                audio_timestamp_end=53.0,
                cultural_markers=["sangat membantu", "Terima kasih banyak"]
            ),
        ]
    ),

    # -------------------------------------------------------------------------
    # INDONESIA SCENARIO 2: Regional Javanese Accent & Restructuring Request
    # -------------------------------------------------------------------------
    ScenarioRecord(
        scenario_id="id_javanese_accent_hardship",
        market_code=MarketCode.INDONESIA,
        title="🇮🇩 ID Call 2: Javanese Regional Accent Customer with Cashflow Delay & Tenor Restructuring",
        description="Customer speaking with regional Javanese vocabulary ('nuwun sewu', 'nggih', 'kula', 'mboten') experiences harvest delay and requests penalty waiver and tenor extension.",
        test_category="regional_accent",
        expected_outcome="Agent understands Javanese dialect markers, responds with deep cultural respect, grants 3-day grace period, and explains OJK tenor extension application.",
        adaptation_highlights=[
            "High comprehension of Javanese regional dialect words ('Nuwun sewu', 'nggih', 'dereng', 'mboten numpuk').",
            "Non-confrontational, respectful Indonesian response matching Javanese cultural politeness.",
            "Proper OJK multifinance restructuring guidance without aggressive threats."
        ],
        timeline=[
            DialogueTurn(
                role=DialogueRole.AGENT,
                speaker_name="Dewi (Agent)",
                text="Selamat siang Bapak Bambang, saya Dewi dari Darwix Multifinance. Mohon maaf mengganggu waktunya sebentar ya Pak, terkait konfirmasi angsuran pembiayaan traktor pertanian Bapak.",
                audio_timestamp_start=0.0,
                audio_timestamp_end=8.0,
                cultural_markers=["Selamat siang", "Bapak", "Mohon maaf"]
            ),
            DialogueTurn(
                role=DialogueRole.CUSTOMER,
                speaker_name="Bambang (Customer - Javanese Accent)",
                text="Nuwun sewu Mbak Dewi... niki kula badhe nyuwun tulung. Panen pari kula rada telat niki, dados arto dereng kumpul. Menawi pembayaran mundur seminggu napa saged mboten dipun denda nggih?",
                audio_timestamp_start=8.5,
                audio_timestamp_end=20.0,
                cultural_markers=["Nuwun sewu", "kula", "badhe nyuwun tulung", "dereng", "nggih"]
            ),
            DialogueTurn(
                role=DialogueRole.AGENT,
                speaker_name="Dewi (Agent)",
                text="Inggih Bapak Bambang, kami sangat memahami situasi panen di daerah Bapak. Sesuai ketentuan, kami berikan masa tenggang denda selama 3 hari kalender ya Pak. Untuk sisa harinya, kami bisa bantu buatkan komitmen tanggal pembayaran khusus.",
                audio_timestamp_start=20.5,
                audio_timestamp_end=33.0,
                cultural_markers=["Inggih Bapak", "masa tenggang", "komitmen pembayaran"]
            ),
            DialogueTurn(
                role=DialogueRole.CUSTOMER,
                speaker_name="Bambang (Customer - Javanese Accent)",
                text="Matur nuwun sanget Mbak Dewi. Lajeng menawi sisa cicilan niki dipun perpanjang tenore mawon supados angsurane saben wulan langkung enteng, napa saged?",
                audio_timestamp_start=33.5,
                audio_timestamp_end=43.5,
                cultural_markers=["Matur nuwun sanget", "perpanjang tenore", "langkung enteng"]
            ),
            DialogueTurn(
                role=DialogueRole.AGENT,
                speaker_name="Dewi (Agent)",
                text="Saged Bapak Bambang, pinter sanget usul Bapak. Kami bisa bantu ajukan program restrukturisasi perpanjangan tenor pembiayaan tambahan 12 bulan agar angsuran per bulannya turun dari 3 Juta menjadi 1,8 Juta saja. Nanti petugas cabang kami yang akan sowan silaturahmi untuk tanda tangan berkas ya Pak.",
                audio_timestamp_start=44.0,
                audio_timestamp_end=58.5,
                cultural_markers=["Saged Bapak", "restrukturisasi", "sowan silaturahmi"]
            ),
            DialogueTurn(
                role=DialogueRole.CUSTOMER,
                speaker_name="Bambang (Customer - Javanese Accent)",
                text="Alhamdulillah, matur suwun sanget Mbak Dewi. Kula tunggu rawuhipun petugas cabang. Mugi-mugi berkah.",
                audio_timestamp_start=59.0,
                audio_timestamp_end=66.0,
                cultural_markers=["Alhamdulillah", "matur suwun sanget", "kula tunggu", "Mugi-mugi berkah"]
            ),
        ]
    )
]
