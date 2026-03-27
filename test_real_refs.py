"""
测试 27 条真实参考文献的检测准确率
目标：95% 以上应判定为 real 或 uncertain（不应误判为 suspicious）
"""
import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from ref_checker.parser import parse_reference
from ref_checker.verifier import verify, STATUS_REAL, STATUS_UNCERTAIN, STATUS_SUSPICIOUS

STATUS_DISPLAY = {STATUS_REAL: "✅ 真实", STATUS_UNCERTAIN: "⚠️  待确认", STATUS_SUSPICIOUS: "❌ 可疑"}

REFS = [
    'Riedinger, D. J.; Hassenrück, C.; Herlemann, D.; Labrenz, M. Global Distribution and Predictive Modeling of Vibrio vulnificus Abundance. Commun. Earth Environ. 2025, 6, 210.',
    'Seymour, J. R.; McLellan, S. L. Climate Change Will Amplify the Impacts of Harmful Microorganisms in Aquatic Ecosystems. Nat. Microbiol. 2025, 10 (3), 615−626.',
    'Brauge, T.; Mougin, J.; Ells, T.; Midelet, G. Sources and Contamination Routes of Seafood with Human Pathogenic Vibrio spp.: A Farm-to-Fork Approach. CRFSFS. 2024, 23 (1), No. e13283.',
    'Brumfield, K. D.; Usmani, M.; Long, D. M.; Lupari, H. A.; Pope, R. K.; Jutla, A. S.; Huq, A.; Colwell, R. R. Climate Change and Vibrio: Environmental Determinants for Predictive Risk Assessment. Proc. Natl. Acad. Sci. U. S. A. 2025, 122 (33), No. e2420423122.',
    'Heng, S. P.; Letchumanan, V.; Deng, C. Y.; Ab Mutalib, N. S.; Khan, T. M.; Chuah, L. H.; Chan, K. G.; Goh, B. H.; Pusparajah, P.; Lee, L. H. Vibrio vulnificus: An Environmental and Clinical Burden. Front. Microbiol. 2017, 8, 997.',
    'Su, Y. C.; Liu, C. Vibrio Parahaemolyticus: A Concern of Seafood Safety. Food Microbiol. 2007, 24 (6), 549−558.',
    'Amaro, C.; Sanjuán, E.; Fouz, B.; Pajuelo, D.; Lee, C. T.; Hor, L. I.; Barrera, R. The Fish Pathogen Vibrio vulnificus Biotype 2: Epidemiology, Phylogeny, and Virulence Factors Involved in Warm Water Vibriosis. Microbiol. Spectrum 2015, 3 (3), 10−1128.',
    'Raghunath, P.; Karunasagar, I.; Karunasagar, I. Improved Isolation and Detection of Pathogenic Vibrio parahaemolyticus from Seafood Using a New Enrichment Broth. Int. J. Food Microbiol. 2009, 129 (2), 200−203.',
    'Cui, X. P.; Zhou, H. B.; Wang, Z. W.; Yang, J.; Lu, Z. X.; Shi, C. Z.; Hu, A. T.; Li, R. L.; Bie, X. M. Establishment and Application of a Multiplex Real-Time PCR Assay Coupled with Propidium Monoazide for the Simultaneous Detection of Viable Vibrio parahaemolyticus, Vibrio vulnificus and Vibrio alginolyticus. Food Contr. 2024, 158, 110251.',
    'Li, Y.; Zhang, S.; Li, J.; Chen, M.; He, M.; Wang, Y.; Zhang, Y.; Jing, H.; Ma, H.; Li, Y.; et al. Application of Digital PCR and Next Generation Sequencing in the Etiology Investigation of a Foodborne Disease Outbreak Caused by Vibrio parahaemolyticus. Food Microbiol. 2019, 84, 103233.',
    'Pang, B.; Zhao, C.; Li, L.; Song, X.; Xu, K.; Wang, J.; Liu, Y.; Fu, K.; Bao, H.; Song, D.; et al. Development of a Low-Cost Paper Based ELISA Method for Rapid Escherichia coli O157:H7 Detection. Anal. Biochem. 2018, 542, 58−62.',
    'Cialla-May, D.; Bonifacio, A.; Bocklitz, T.; Markin, A.; Markina, N.; Fornasaro, S.; Dwivedi, A.; Dib, T.; Farnesi, E.; Liu, C.; et al. Biomedical SERS-The Current State and Future Trends. Chem. Soc. Rev. 2024, 53 (18), 8957−8979.',
    'Brumfield, K. D.; Chen, A. J.; Gangwar, M.; Usmani, M.; Hasan, N. A.; Jutla, A. S.; Huq, A.; Colwell, R. R. Environmental Factors Influencing Occurrence of Vibrio parahaemolyticus and Vibrio vulnificus. Appl. Environ. Microbiol. 2023, 89 (6), No. e0030723.',
    'Randa, M. A.; Polz, M. F.; Lim, E. Effects of Temperature and Salinity on Vibrio vulnificus Population Dynamics as Assessed by Quantitative PCR. Appl. Environ. Microbiol. 2004, 70 (9), 5469−5476.',
    'Wang, M.; Li, L.; Wei, L.; Han, Y.; Chen, Y. Multiplexed Pathogenic Bacteria Detection via a Two-Dimensional Encoded Fluorescent Microsphere System. Nano Lett. 2025, 25 (6), 2256−2265.',
    'Peng, W. P.; Liu, Y. J.; Lu, M. H.; Li, X. Y.; Liang, Y. T.; Wang, R. M.; Zhang, W. L.; Man, S. L.; Ma, L. Advances in Surface Enhanced Raman Scattering Detection of Foodborne Pathogens: From Recognition-Based Fingerprint to Molecular Diagnosis. Coord. Chem. Rev. 2024, 518, 216083.',
    'Wu, G.; Zhu, R.; Lu, Y.; Hong, M.; Xu, F. Optical Scanning Endoscope via a Single Multimode Optical Fiber. Opto-Electron. Sci. 2024, 3 (3), 230041.',
    'Qadri, F.; Svennerholm, A. M.; Faruque, A. S.; Sack, R. B. Enterotoxigenic Escherichia coli in Developing Countries: Epidemiology, Microbiology, Clinical features, Treatment, and Prevention. Clin. Microbiol. Rev. 2005, 18 (3), 465−483.',
    'Xu, Y.; Sun, R.; Zheng, Z.; Ye, L.; Peng, M.; Chen, S. Genomic and Phenotypic Analysis of Virulence, Antimicrobial Resistance, and Transmission Routes of Vibrio vulnificus from Food and Clinical Sources in China. Food Res. Int. 2025, 220, 117148.',
    'Roy, P. K.; Roy, A.; Jeon, E. B.; DeWitt, C. A. M.; Park, J. W.; Park, S. Y. Comprehensive Analysis of Predominant Pathogenic Bacteria and Viruses in Seafood Products. CRFSFS. 2024, 23 (4), No. e13410.',
    'Tsai, Y. H.; Wen-Wei Hsu, R.; Huang, K. C.; Huang, T. J. Comparison of Necrotizing Fasciitis and Sepsis Caused by Vibrio vulnificus and Staphylococcus aureus. JBJS. 2011, 93 (3), 274−284.',
    'Yang, F.; Jiang, Y.; Yang, L.; Qin, J.; Guo, M.; Lu, Y.; Chen, H.; Zhuang, Y.; Zhang, J.; Zhang, H.; et al. Molecular and Conventional Analysis of Acute Diarrheal Isolates Identifies Epidemiological Trends, Antibiotic Resistance and Virulence Profiles of Common Enteropathogens in Shanghai. Front. Microbiol. 2018, 9, 164.',
    'Humphries, R. M.; Linscott, A. J. Practical Guidance for Clinical Microbiology Laboratories: Diagnosis of Bacterial Gastroenteritis. Clin. Microbiol. Rev. 2015, 28 (1), 3−31.',
    'Bosi, E.; Taviani, E.; Avesani, A.; Doni, L.; Auguste, M.; Oliveri, C.; Leonessi, M.; Martinez-Urtaza, J.; Vetriani, C.; Vezzulli, L. Pan Genome Provides Insights into Vibrio Evolution and Adaptation to Deep-Sea Hydrothermal Vents. Genome Biol. Evol. 2024, 16 (7), No. evae131.',
    'Lin, H.; Yu, M.; Wang, X.; Zhang, X. H. Comparative Genomic Analysis Reveals the Evolution and Environmental Adaptation Strategies of Vibrios. BMC genomics 2018, 19 (1), 135.',
    'López-Pérez, M.; Jayakumar, J. M.; Grant, T. A.; Zaragoza Solas, A.; Cabello-Yeves, P. J.; Almagro-Moreno, S. Ecological Diversification Reveals Routes of Pathogen Emergence in Endemic Vibrio vulnificus Populations. Proc. Natl. Acad. Sci. U. S. A. 2021, 118 (40), No. e2103470118.',
    'Hoefler, F.; Pouget-Abadie, X.; Roncato-Saberan, M.; Lemarié, R.; Takoudju, E. M.; Raffi, F.; Corvec, S.; Le Bras, M.; Cazanave, C.; Lehours, P.; et al. Clinical and Epidemiologic Characteristics and Therapeutic Management of Patients with Vibrio Infections, Bay of Biscay, France, 2001−2019. Emerg. Infect. Dis. 2022, 28 (12), 2367−2373.',
]

if __name__ == "__main__":
    print("=" * 70)
    print(f"  真实文献检测测试：{len(REFS)} 条")
    print("  期望：real 或 uncertain（不应误判为 suspicious）")
    print("=" * 70)

    correct = 0
    failed = []

    for i, text in enumerate(REFS, 1):
        ref = parse_reference(text)
        result = verify(ref)
        status = STATUS_DISPLAY.get(result.status, "?")
        hit = result.status in {STATUS_REAL, STATUS_UNCERTAIN}
        correct += hit
        mark = "√" if hit else "✗"

        # 简洁输出
        short = text[:75] + "..." if len(text) > 75 else text
        print(f"  [{i:2d}] {mark}  {status}  {result.confidence:.0%}  {short}")
        if not hit:
            failed.append((i, text, result))

    rate = correct / len(REFS)
    print(f"\n{'=' * 70}")
    print(f"  通过: {correct}/{len(REFS)} ({rate:.0%})")
    print(f"  目标: 95% ({'✅ 达标' if rate >= 0.95 else '❌ 未达标'})")
    print(f"{'=' * 70}")

    if failed:
        print(f"\n  --- 误判详情 ---")
        for idx, text, result in failed:
            ref = parse_reference(text)
            print(f"\n  [{idx}] {text[:90]}...")
            print(f"       解析标题: {ref.title}")
            print(f"       匹配标题: {result.evidence_title}")
            print(f"       置信度: {result.confidence:.2f}")
            print(f"       说明: {result.message}")
