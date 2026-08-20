"""
Localized Regulatory Knowledge & Banking Policies for Philippines & Indonesia Voice Bots
"""

from typing import Dict, Any, List
from backend.app.q3_multilingual_bots.models import MarketCode

LOCALIZED_KNOWLEDGE: Dict[MarketCode, Dict[str, Any]] = {
    MarketCode.PHILIPPINES: {
        "regulatory_body": "Insurance Commission (IC) of the Philippines",
        "sector": "Bancassurance & Life Insurance",
        "currency": "Philippine Peso (₱ / PHP)",
        "policies": [
            {
                "topic": "Grace Period & Policy Lapse",
                "rules": "All individual life insurance policies carry a statutory 31-day grace period from the premium due date. If unpaid after 31 days, the policy lapses, but can be reinstated within 3 years subject to insurability."
            },
            {
                "topic": "Bancassurance Cross-Sell Riders",
                "rules": "Available riders include: Hospital Income Benefit (₱1,000 to ₱5,000 daily cash allowance during confinement), Critical Illness Cover (up to 56 conditions), and Accidental Death & Dismemberment (AD&D 100% additional payout)."
            },
            {
                "topic": "Payment Channels & Modes",
                "rules": "Accepted via Bancassurance Auto-Debit (ADA), Online Banking (BDO, BPI, Metrobank, Maya, GCash), and Over-the-counter branch teller. Premium modes: Monthly, Quarterly, Semi-Annual, Annual (5% discount on annual)."
            },
            {
                "topic": "Anti-Rebating Compliance",
                "rules": "Under IC circular, agents and bots are strictly prohibited from offering commission rebates or unauthorized cash gifts to induce insurance purchases."
            }
        ]
    },
    MarketCode.INDONESIA: {
        "regulatory_body": "Otoritas Jasa Keuangan (OJK) Republik Indonesia",
        "sector": "Multifinance & Consumer Vehicle Financing",
        "currency": "Indonesian Rupiah (Rp / IDR)",
        "policies": [
            {
                "topic": "Jatuh Tempo & Grace Period Denda",
                "rules": "Tanggal jatuh tempo tercantum pada kontrak perjanjian pembiayaan. Terdapat grace period 3 hari kalender sebelum denda keterlambatan (0.5% per hari dari nilai angsuran) mulai dihitung."
            },
            {
                "topic": "Restrukturisasi & Perpanjangan Tenor",
                "rules": "Sesuai regulasi OJK, debitur yang mengalami penurunan kemampuan finansial dapat mengajukan restrukturisasi pembiayaan berupa perpanjangan tenor (maksimal tambahan 12-24 bulan) atau rescheduling tanggal jatuh tempo."
            },
            {
                "topic": "Pelunasan Dipercepat & Pengambilan BPKB",
                "rules": "Pelunasan dipercepat dikenakan biaya administrasi 2% dari sisa pokok pinjaman. Dokumen jaminan BPKB asli dapat diambil di kantor cabang 3 hari kerja setelah pelunasan diverifikasi lunas."
            },
            {
                "topic": "Saluran Pembayaran Resmi",
                "rules": "Pembayaran angsuran dapat dilakukan melalui Virtual Account (BCA, Mandiri, BRI, BNI), Indomaret/Alfamart, dan aplikasi e-wallet (GoPay, OVO, ShopeePay)."
            }
        ]
    }
}
