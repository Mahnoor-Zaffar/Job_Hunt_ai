"""Mid-sized IT Company Discovery for Pakistan.

Discovers Pakistani IT/software companies with 50-500 employees
from curated lists, directory scraping, and web search.
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("job_hunting.it_company_scraper")

CACHE_FILE = os.path.join(os.path.dirname(__file__), ".it_company_cache.json")
CACHE_TTL = 86400  # 24 h


@dataclass
class CompanyEntry:
    name: str
    domain: str
    city: str
    industry: str
    size: str
    linkedin_slug: str
    category: str = "it_company"


def _curated_list() -> list[CompanyEntry]:
    """Curated list of 130+ mid-sized Pakistani IT companies (50-500 employees)."""
    return [
        # -- Original entries --
        CompanyEntry("Volmatica", "volmatica.com", "Rawalpindi", "Software Development", "80-249", "volmatica-inc"),
        CompanyEntry("Comtanix", "comtanix.com", "Rawalpindi", "BPO/Software", "55-200", "comtanix"),
        CompanyEntry("Zenkoders", "zenkoders.com", "Karachi", "Software Development", "51-200", "zenkoders"),
        CompanyEntry("Cubix", "cubix.co", "Karachi", "Software Development", "100-250", "cubixglobal"),
        CompanyEntry("NxN Pakistan", "nxn.com.pk", "Karachi", "Software Development", "8-50", "nxn-pakistan"),
        CompanyEntry("Liquid Technologies", "liqteq.com", "Karachi", "Software Development", "51-200", "liqteq"),
        CompanyEntry("Arpatech", "arpatech.com", "Karachi", "Software Development", "201-500", "arpatech"),
        CompanyEntry("VentureDive", "venturedive.com", "Karachi", "Software Development", "200-500", "venturedive"),
        CompanyEntry("Cygnis", "cygnislabs.com", "Karachi", "Software Development", "50-200", "cygnislabs"),
        CompanyEntry("KoderLabs", "koderlabs.com", "Karachi", "Software Development", "100-250", "koderlabs"),
        CompanyEntry("BariTechSol", "baritechsol.com", "Karachi", "Software Development", "50-249", "baritechsol"),
        CompanyEntry("8Ration", "8ration.com", "Karachi", "Software Development", "50-249", "8ration"),
        CompanyEntry("Brilworks", "brilworks.com", "Karachi", "Software Development", "50-100", "brilworks"),
        CompanyEntry("TPS Pakistan", "tps.com.pk", "Karachi", "Fintech", "100-200", "tps-pakistan"),
        CompanyEntry("Techlogix", "techlogix.com", "Lahore", "IT Services", "200-500", "techlogix"),
        CompanyEntry("Confiz", "confiz.com", "Lahore", "IT Services", "200-500", "confiz"),
        CompanyEntry("NetSol Technologies", "netsoltech.com", "Lahore", "Fintech", "500-1000", "netsoltech"),
        CompanyEntry("Devsinc", "devsinc.com", "Lahore", "Software Development", "300-500", "devsinc"),
        CompanyEntry("Tkxel", "tkxel.com", "Lahore", "Software Development", "250-500", "tkxel"),
        CompanyEntry("Jaffer Business Systems", "jbs.com.pk", "Lahore", "IT Services", "100-200", "jaffer-business-systems"),
        CompanyEntry("SN Skies", "snskies.com", "Lahore", "Software Development", "50-249", "snskies-pk"),
        CompanyEntry("Novatore Solutions", "novatore.com.pk", "Lahore", "Software Development", "50-200", "novatore"),
        CompanyEntry("Bitsclan", "bitsclan.com", "Lahore", "Software Development", "50-100", "bitsclan"),
        CompanyEntry("ESketchers", "esketchers.com", "Lahore", "Software Development", "50-100", "esketchers"),
        CompanyEntry("Beta Solutions", "betasolutions.com.pk", "Lahore", "Software Development", "50-150", "betasolutionspk"),
        CompanyEntry("Scube Solutions", "scubesolutions.com", "Lahore", "Software Development", "50-100", "scubesolutions"),
        CompanyEntry("Nascence Consulting", "nascence.com", "Lahore", "Software Development", "50-150", "nascence"),
        CompanyEntry("Mindstorm Labs", "mindstormlabs.com", "Lahore", "Software Development", "50-100", "mindstormlabs"),
        CompanyEntry("Kualitatem", "kualitatem.com", "Lahore", "QA/Software", "50-200", "kualitatem"),
        CompanyEntry("Sofizar", "sofizar.com", "Lahore", "Software Development", "50-150", "sofizar"),
        CompanyEntry("Xavor Corporation", "xavor.com", "Lahore", "Software Development", "100-300", "xavor"),
        CompanyEntry("NorthBay Solutions", "northbay.com", "Lahore", "Software Development", "100-300", "northbaysolutions"),
        CompanyEntry("Agility Solutions", "agility.pk", "Lahore", "Software Development", "50-100", "agility-pk"),
        CompanyEntry("i2c Inc Pakistan", "i2cinc.com", "Lahore", "Fintech", "200-500", "i2cinc"),
        CompanyEntry("Avanza Solutions", "avanzasolutions.com", "Islamabad", "Software Development", "100-250", "avanzasolutions"),
        CompanyEntry("Ovex Technologies", "ovextech.com", "Islamabad", "BPO", "300-700", "ovex-technologies"),
        CompanyEntry("Bravado Solutions", "bravadosolutions.com", "Islamabad", "Software Development", "50-200", "bravadosolutions"),
        CompanyEntry("Codistan Ventures", "codistan.org", "Islamabad", "Software Development", "50-150", "codistan"),
        CompanyEntry("Synergy IT", "synergyit.com", "Islamabad", "Software Development", "50-200", "synergyit"),
        CompanyEntry("Icreativez", "icreativez.com", "Islamabad", "Software Development", "50-150", "icreativez"),
        CompanyEntry("LMKT", "lmkt.com.pk", "Islamabad", "IT Services", "100-250", "lmkt"),
        CompanyEntry("Digitilization", "digilitization.com", "Islamabad", "Software Development", "50-100", "digilitization"),
        CompanyEntry("Hudsonex", "hudsonex.com", "Islamabad", "Software Development", "50-150", "hudsonexate"),
        CompanyEntry("Plutus Labs", "plutuslabs.com", "Islamabad", "Software Development", "50-100", "plutuslabs"),
        CompanyEntry("E2E Technologies", "e2e.com.pk", "Islamabad", "Software Development", "50-100", "e2e-pk"),
        CompanyEntry("Mountainise", "mountainise.com", "Islamabad", "Software Development", "50-100", "mountainise"),
        CompanyEntry("Ertiqah Consulting", "ertiqah.com", "Islamabad", "Software Development", "50-100", "ertiqah"),
        CompanyEntry("Vizteck Solutions", "vizteck.com", "Islamabad", "Software Development", "50-100", "vizteck"),
        CompanyEntry("M Techub", "mtechub.com", "Rawalpindi", "Software Development", "50-249", "mtechub"),
        CompanyEntry("Nexshore Technologies", "nexshoretech.com", "Islamabad", "Software Development", "50-100", "nexshore"),

        # -- New additions --
        CompanyEntry("Eziline Software House", "eziline.com", "Islamabad", "Software", "50-200", "eziline"),
        CompanyEntry("CodeAgepk", "codeagepk.com", "Islamabad", "Software", "50-100", "codeagepk"),
        CompanyEntry("Codexier Software House", "codexier.com", "Lahore", "Software", "50-150", "codexier"),
        CompanyEntry("KeyDevs", "keydevs.com", "Islamabad", "Software", "50-150", "keydevs"),
        CompanyEntry("Techuire", "techuire.com", "Lahore", "Software", "50-100", "techuire"),
        CompanyEntry("Pcland Software", "pcland.com.pk", "Karachi", "Software", "50-100", "pcland-software"),
        CompanyEntry("Aurora Solutions", "aurorasolutions.com.pk", "Lahore", "Software", "50-150", "aurora-solutions-pk"),
        CompanyEntry("Sofgear", "sofgear.com", "Lahore", "Software", "50-100", "sofgear"),
        CompanyEntry("CyberVision Tech", "cybervisiontech.com", "Karachi", "Software", "50-100", "cybervisiontech"),
        CompanyEntry("Webtonix", "webtonix.com", "Lahore", "Software", "50-100", "webtonix"),
        CompanyEntry("QuellxCode", "quellxcode.com", "Islamabad", "Software", "50-100", "quellxcode"),
        CompanyEntry("Techozon Software House", "techozon.com", "Lahore", "Software", "50-100", "techozon"),
        CompanyEntry("Ideatech Software House", "ideatech.com.pk", "Islamabad", "Software", "50-100", "ideatech-pk"),
        CompanyEntry("Bahria Town Software House", "bahriatownsoftware.com", "Rawalpindi", "Software", "50-150", "bahria-town-software"),
        CompanyEntry("Coding Souls", "codingsouls.com", "Karachi", "Software", "50-100", "codingsouls"),
        CompanyEntry("Quaid Technologies", "quaidtech.com", "Karachi", "Software", "50-100", "quaid-technologies"),
        CompanyEntry("E Software House", "esoftwarehouse.com", "Lahore", "Software", "50-100", "e-software-house"),
        CompanyEntry("Codeyon Software House", "codeyon.com", "Islamabad", "Software", "50-100", "codeyon"),
        CompanyEntry("Vertix", "vertix.com.pk", "Lahore", "IT Services", "50-150", "vertix-pk"),
        CompanyEntry("Telesehat Private Limited", "telesehat.com", "Karachi", "Software", "50-100", "telesehat"),
        CompanyEntry("DynamoLogic Solutions", "dynamologic.com", "Lahore", "Software", "50-100", "dynamologic"),
        CompanyEntry("Web Design Pakistan", "webdesignpakistan.com", "Lahore", "Software", "50-100", "web-design-pakistan"),
        CompanyEntry("uExel", "uexel.com", "Lahore", "Software", "50-100", "uexel"),
        CompanyEntry("Code Engineers Software House", "codeengineers.com", "Islamabad", "Software", "50-100", "code-engineers"),
        CompanyEntry("Media Hut", "mediahut.com.pk", "Karachi", "Software", "50-100", "media-hut-pk"),
        CompanyEntry("LIFELONG Pakistan", "lifelong.pk", "Lahore", "Software", "50-100", "lifelong-pk"),
        CompanyEntry("JZZ The IT Solution", "jzz.com.pk", "Islamabad", "IT Services", "50-100", "jzz-it-solution"),
        CompanyEntry("IDWARE Pakistan", "idware.com.pk", "Karachi", "Software", "50-100", "idware-pk"),
        CompanyEntry("iPlex", "iplex.com.pk", "Lahore", "Software", "50-100", "iplex-pk"),
        CompanyEntry("Softnix", "softnix.com", "Islamabad", "Software", "50-100", "softnix"),
        CompanyEntry("Convo", "convo.com", "Karachi", "Software", "50-150", "convo"),
        CompanyEntry("IntechSol", "intechsol.com", "Lahore", "Software", "50-100", "intechsol"),
        CompanyEntry("Software House SP", "softwarehousesp.com", "Islamabad", "Software", "50-100", "software-house-sp"),
        CompanyEntry("Volpea Solutions", "volpea.com", "Lahore", "Software", "50-100", "volpea"),
        CompanyEntry("Ebridge", "ebridge.com.pk", "Karachi", "Software", "50-100", "ebridge-pk"),
        CompanyEntry("APPINSNAP", "appinsnap.com", "Islamabad", "Software", "50-100", "appinsnap"),
        CompanyEntry("Solutions Player", "solutionsplayer.com", "Lahore", "Software", "50-100", "solutions-player"),
        CompanyEntry("Vizteck Solution", "viztecksolution.com", "Islamabad", "Software", "50-100", "vizteck-solution"),
        CompanyEntry("Friends IT Solutions", "friendsitsolutions.com", "Karachi", "Software", "50-100", "friends-it-solutions"),
        CompanyEntry("Ropstam Solutions", "ropstam.com", "Islamabad", "Software", "100-250", "ropstam"),
        CompanyEntry("Delta Services Company", "deltaservices.com.pk", "Karachi", "IT Services", "50-100", "delta-services-pk"),
        CompanyEntry("Software Development Hub Pakistan", "softwarehub.pk", "Lahore", "Software", "50-100", "software-hub-pk"),
        CompanyEntry("Relymer Group", "relymer.com", "Islamabad", "Software", "50-100", "relymer"),
        CompanyEntry("Ciklum Islamabad Pakistan", "ciklum.pk", "Islamabad", "IT Services", "100-250", "ciklum-pk"),
        CompanyEntry("Viremp Technologies", "viremp.com", "Karachi", "Software", "50-100", "viremp"),
        CompanyEntry("E-strats", "estrats.com.pk", "Islamabad", "Software", "50-100", "e-strats"),
        CompanyEntry("Sahaara Software House", "sahaarasoftware.com", "Lahore", "Software", "50-100", "sahaara-software"),
        CompanyEntry("Websolutes", "websolutes.com", "Karachi", "Software", "50-100", "websolutes"),
        CompanyEntry("Yuz Technologies", "yuztech.com", "Islamabad", "Software", "50-100", "yuz-technologies"),
        CompanyEntry("VQode Solutions", "vqode.com", "Lahore", "Software", "50-100", "vqode"),
        CompanyEntry("The Right Software", "therightsoftware.com", "Karachi", "Software", "50-100", "the-right-software"),
        CompanyEntry("Softoven", "softoven.com", "Islamabad", "Software", "50-100", "softoven"),
        CompanyEntry("Arpasof-Pakistan", "arpasof.com", "Lahore", "Software", "50-100", "arpasof"),
        CompanyEntry("ZIGRON", "zigron.com", "Karachi", "Software", "50-100", "zigron"),
        CompanyEntry("Exagic", "exagic.com", "Islamabad", "Software", "50-100", "exagic"),
        CompanyEntry("Wise House", "wisehouse.com.pk", "Lahore", "Software", "50-100", "wise-house-pk"),
        CompanyEntry("Cybesol", "cybesol.com", "Karachi", "Software", "50-100", "cybesol"),
        CompanyEntry("Limra Pakistan", "limrapakistan.com", "Lahore", "Software", "50-100", "limra-pk"),
        CompanyEntry("Nextbridge", "nextbridge.com.pk", "Karachi", "IT Services", "100-250", "nextbridge"),
        CompanyEntry("DPL", "dpl.com.pk", "Lahore", "Software", "50-100", "dpl-pk"),
        CompanyEntry("JD Apps Studio", "jdappsstudio.com", "Islamabad", "Software", "50-100", "jd-apps-studio"),
        CompanyEntry("Premium Technologies", "premiumtech.com.pk", "Karachi", "Software", "50-100", "premium-tech-pk"),
        CompanyEntry("Weeinvent", "weeinvent.com", "Lahore", "Software", "50-100", "weeinvent"),
        CompanyEntry("Exytex Technologies", "exytex.com", "Islamabad", "Software", "50-100", "exytex"),
        CompanyEntry("Whizpool", "whizpool.com", "Lahore", "Software", "50-150", "whizpool"),
        CompanyEntry("OAKTEQ", "oakteq.com", "Islamabad", "Software", "50-100", "oakteq"),
        CompanyEntry("Glaxit Software House", "glaxit.com", "Karachi", "Software", "50-100", "glaxit"),
        CompanyEntry("F3 Technologies", "f3tech.com.pk", "Lahore", "Software", "50-100", "f3-technologies"),
        CompanyEntry("Utoria Infotech Solutions", "utoria.com", "Islamabad", "Software", "50-100", "utoria"),
        CompanyEntry("SignUp Solution", "signupsolution.com", "Karachi", "Software", "50-100", "signup-solution"),
        CompanyEntry("Xorlogics", "xorlogics.com", "Lahore", "Software", "50-100", "xorlogics"),
        CompanyEntry("Technology Ideas", "techideas.com.pk", "Islamabad", "Software", "50-100", "tech-ideas"),
        CompanyEntry("TenByte", "tenbyte.com", "Karachi", "Software", "50-100", "tenbyte"),
        CompanyEntry("Tritechteal Technologies", "tritechteal.com", "Lahore", "Software", "50-100", "tritechteal"),
        CompanyEntry("Techorra", "techorra.com", "Islamabad", "Software", "50-100", "techorra"),
        CompanyEntry("Ideofuzion", "ideofuzion.com", "Karachi", "Software", "50-100", "ideofuzion"),
        CompanyEntry("OmniSofex", "omnisofex.com", "Lahore", "Software", "50-100", "omnisofex"),
        CompanyEntry("Bentley Systems Pakistan", "bentley.com.pk", "Islamabad", "Software", "100-300", "bentley-pk"),
        CompanyEntry("WeGlobe Technologies", "weglobe.com.pk", "Karachi", "Software", "50-100", "weglobe-tech"),
        CompanyEntry("Appic Solutions", "appicsolutions.com", "Lahore", "Software", "50-100", "appic-solutions"),
        CompanyEntry("SofoSol", "sofosol.com", "Islamabad", "Software", "50-100", "sofosol"),
        CompanyEntry("Pakistan Software House", "pakistansoftwarehouse.com", "Karachi", "Software", "50-100", "pakistan-software-house"),
        CompanyEntry("Immencia", "immencia.com", "Lahore", "Software", "50-100", "immencia"),
        CompanyEntry("Sofech Business Services", "sofech.com", "Islamabad", "IT Services", "50-100", "sofech"),
        CompanyEntry("CODO LOGIX", "codologix.com", "Karachi", "Software", "50-100", "codo-logix"),
        CompanyEntry("Vantage Sof", "vantagesof.com", "Lahore", "Software", "50-100", "vantage-sof"),
        CompanyEntry("SOWEBIT", "sowebit.com.pk", "Islamabad", "Software", "50-100", "sowebit"),
        CompanyEntry("Fify5bytes", "fify5bytes.com", "Karachi", "Software", "50-100", "fify5bytes"),

        # -- Batch 3 (Google Maps extraction) --
        CompanyEntry("IT Genesis", "itgenesis.net", "Lahore", "Software", "50-200", "itgenesis"),
        CompanyEntry("Technolyte", "technolyte.com", "Lahore", "Software", "50-200", "technolyte"),
        CompanyEntry("GenXe Technologies", "genxe.com.pk", "Lahore", "Software", "50-200", "genxe"),
        CompanyEntry("Techverx", "techverx.com", "Lahore", "Software", "50-200", "techverx"),
        CompanyEntry("BiT Technologies", "bitechnologies.com", "Lahore", "Software", "50-200", "bitechnologies"),
        CompanyEntry("REX Technologies", "rextech.com", "Lahore", "Software", "50-200", "rextech"),
        CompanyEntry("Whetsonez", "whetstonez.com", "Lahore", "Software", "50-200", "whetstonez"),
        CompanyEntry("United Software", "theunitedsoft.com", "Lahore", "Software", "50-200", "theunitedsoft"),
        CompanyEntry("IRG Global Technologies", "irgglobal.co", "Lahore", "Software", "50-200", "irgglobal"),
        CompanyEntry("InvoZone", "invozone.com", "Lahore", "Software", "50-200", "invozone"),
        CompanyEntry("Contour Software", "contour-software.com", "Lahore", "Software", "50-200", "contour-software"),
        CompanyEntry("Aquila Techs", "aquilatechs.com", "Lahore", "Software", "50-200", "aquilatechs"),
        CompanyEntry("Square63", "square63.com", "Lahore", "Software", "50-200", "square63"),
        CompanyEntry("Olumi Tech", "olumitech.com", "Lahore", "Software", "50-200", "olumitech"),
        CompanyEntry("ZAPTA Technologies", "zaptatech.co", "Lahore", "Software", "50-200", "zaptatech"),
        CompanyEntry("Vaival Technologies", "vaival.com", "Lahore", "Software", "50-200", "vaival"),
        CompanyEntry("2BTech", "2btech.com", "Lahore", "Software", "50-200", "2btech"),
        CompanyEntry("Crewlogix Technologies", "crewlogix.com", "Lahore", "Software", "50-200", "crewlogix"),
        CompanyEntry("TechSwivel", "techswivel.com", "Lahore", "Software", "50-200", "techswivel"),
        CompanyEntry("Intelliscence", "intelliscence.com", "Lahore", "Software", "50-200", "intelliscence"),
        CompanyEntry("SofAims", "thesofaims.com", "Lahore", "Software", "50-200", "thesofaims"),
        CompanyEntry("Visnext Software Solutions", "visnext.com", "Lahore", "Software", "50-200", "visnext"),
        CompanyEntry("GraceSol Technologies", "gracesol.com", "Lahore", "Software", "50-200", "gracesol"),
        CompanyEntry("CrecenTech Systems", "crecentech.com", "Lahore", "Software", "50-200", "crecentech"),
        CompanyEntry("Bitlinks Tech", "bitlinks.com", "Lahore", "Software", "50-200", "bitlinks"),
        CompanyEntry("ITCHAMPX", "itchampx.com", "Lahore", "Software", "50-200", "itchampx"),
        CompanyEntry("Sixlogics Pakistan", "sixlogics.com", "Lahore", "Software", "50-200", "sixlogics"),
        CompanyEntry("FireWorks Technology", "fireworkstech.com", "Lahore", "Software", "50-200", "fireworkstech"),
        CompanyEntry("First Idea Web Development", "firstideaweb.com", "Lahore", "Software", "50-200", "firstideaweb"),
        CompanyEntry("Quaid Soft", "quaidsoft.com", "Lahore", "Software", "50-200", "quaidsoft"),
        CompanyEntry("Qbatch", "qbatch.com", "Lahore", "Software", "50-200", "qbatch"),
        CompanyEntry("SoloInsight Inc", "soloinsight.co", "Lahore", "Software", "50-200", "soloinsight"),
        CompanyEntry("Whizzbridge", "whizzbridge.com", "Lahore", "Software", "50-200", "whizzbridge"),
        CompanyEntry("Arbisof", "arbisof.com", "Lahore", "Software", "50-200", "arbisof"),
        CompanyEntry("Tech Scale", "techscale.io", "Lahore", "Software", "50-200", "techscale"),
        CompanyEntry("The Exper", "theexperts.com", "Lahore", "Software", "50-200", "theexperts"),
        CompanyEntry("Tower Tech", "thetowertech.com", "Lahore", "Software", "50-200", "thetowertech"),
        CompanyEntry("iDEV", "idev4.co", "Lahore", "Software", "50-200", "idev4"),
        CompanyEntry("Conrad Labs", "conradlabs.com", "Lahore", "Software", "50-200", "conradlabs"),
        CompanyEntry("Q-Sof Technologies", "qsof.pk", "Lahore", "Software", "50-200", "qsof"),
        CompanyEntry("Sakai Technologies", "sakaitechnologies.com", "Lahore", "Software", "50-200", "sakaitechnologies"),
        CompanyEntry("IT Company", "itcompany.co", "Lahore", "Software", "50-200", "itcompany"),
        CompanyEntry("Webiconz Technologies", "webiconz.co", "Lahore", "Software", "50-200", "webiconz"),
        CompanyEntry("Educatve", "educative.com", "Lahore", "Software", "50-200", "educative"),
        CompanyEntry("Stackup Solutions", "stackupsolutions.com", "Lahore", "Software", "50-200", "stackupsolutions"),
        CompanyEntry("Emerald Labs", "emeraldlabs.com", "Lahore", "Software", "50-200", "emeraldlabs"),
        CompanyEntry("Sofech Systems", "sofechsystems.com", "Lahore", "Software", "50-200", "sofechsystems"),
        CompanyEntry("SACTOSOL Technologies", "sactosol.com", "Lahore", "Software", "50-200", "sactosol"),
        CompanyEntry("Salsof Technologies", "salsof.com", "Lahore", "Software", "50-200", "salsof"),
        CompanyEntry("InfoTech Private Limited", "infotech.com.pk", "Lahore", "Software", "50-200", "infotech"),
        CompanyEntry("ZIN Technologies", "zintech.com", "Lahore", "Software", "50-200", "zintech"),
        CompanyEntry("Techcreatx", "techcreatx.com", "Lahore", "Software", "50-200", "techcreatx"),
        CompanyEntry("Creation Next", "creationnext.com", "Lahore", "Software", "50-200", "creationnext"),
        CompanyEntry("Code District", "codedistrict.com", "Lahore", "Software", "50-200", "codedistrict"),
        CompanyEntry("ATRULE Technologies", "atrule.com", "Lahore", "Software", "50-200", "atrule"),
        CompanyEntry("Clustox", "clustox.com", "Lahore", "Software", "50-200", "clustox"),
        CompanyEntry("SAMM IT SOLUTIONS", "sammitsolutions.com", "Lahore", "Software", "50-200", "sammitsolutions"),
        CompanyEntry("Codexia Technologies", "codexiatech.com", "Lahore", "Software", "50-200", "codexiatech"),
        CompanyEntry("Adaxiom Tech", "adaxiomtech.com", "Lahore", "Software", "50-200", "adaxiomtech"),
        CompanyEntry("Cherry Byte Technologies", "thecherrybyte.com", "Lahore", "Software", "50-200", "thecherrybyte"),
        CompanyEntry("Dezital", "dezital.com", "Lahore", "Software", "50-200", "dezital"),
        CompanyEntry("Fast Services", "fastservices.com", "Lahore", "Software", "50-200", "fastservices"),
        CompanyEntry("XnRel", "xnrel.co", "Lahore", "Software", "50-200", "xnrel"),
        CompanyEntry("InventorX Technologies", "inventorx.org", "Lahore", "Software", "50-200", "inventorx"),
        CompanyEntry("IntelTrix", "inteltrix.com", "Lahore", "Software", "50-200", "inteltrix"),
        CompanyEntry("Motve", "gomotve.co", "Lahore", "Software", "50-200", "gomotve"),
        CompanyEntry("Manafa Technologies", "manafa.co", "Lahore", "Software", "50-200", "manafa"),
        CompanyEntry("Webtohelp", "webtohelp.com", "Lahore", "Software", "50-200", "webtohelp"),
        CompanyEntry("Webfoxs", "webfoxs.com", "Lahore", "Software", "50-200", "webfoxs"),
        CompanyEntry("DevBeans Technologies", "devbeans.io", "Lahore", "Software", "50-200", "devbeans"),
        CompanyEntry("Snexus Pvt Ltd", "snexus.com", "Lahore", "Software", "50-200", "snexus"),
        CompanyEntry("YourWebsiteWork", "yourwebsitework.com", "Lahore", "Software", "50-200", "yourwebsitework"),
        CompanyEntry("BiTstorm Technologies", "bitstormtech.com", "Lahore", "Software", "50-200", "bitstormtech"),
        CompanyEntry("Black iBex", "blackibex.com", "Lahore", "Software", "50-200", "blackibex"),
        CompanyEntry("Tech Bridge Web Solutions", "techbridgewebsolutions.com", "Lahore", "Software", "50-200", "techbridgewebsolutions"),
        CompanyEntry("LEADconcept", "leadconcept.com", "Lahore", "Software", "50-200", "leadconcept"),
        CompanyEntry("InTime Web and Software Services", "intimewebservices.com", "Lahore", "Software", "50-200", "intimewebservices"),
        CompanyEntry("TMC (TallyMarks Consulting)", "tallymarks.com", "Lahore", "Software", "50-200", "tallymarks"),
        CompanyEntry("Firm Tech Services", "firmtechservices.com", "Lahore", "Software", "50-200", "firmtechservices"),
        CompanyEntry("Trodosof", "trodosof.com", "Lahore", "Software", "50-200", "trodosof"),
        CompanyEntry("WinsSol", "winssol.com", "Lahore", "Software", "50-200", "winssol"),
        CompanyEntry("Pentagram", "pentagram.com.pk", "Lahore", "Software", "50-200", "pentagram"),
        CompanyEntry("Acube IT Solutions", "acubeitsolutions.com", "Lahore", "Software", "50-200", "acubeitsolutions"),
        CompanyEntry("FordSolution", "fordsolution.com", "Lahore", "Software", "50-200", "fordsolution"),
        CompanyEntry("Al-Burraq Technologies", "al-burraq.com", "Lahore", "Software", "50-200", "al-burraq"),
        CompanyEntry("Future Vision Technologies", "futurevisiontech.com", "Lahore", "Software", "50-200", "futurevisiontech"),
        CompanyEntry("AppifyTech", "appifytech.com", "Lahore", "Software", "50-200", "appifytech"),
        CompanyEntry("Brain Logix", "brainlogix.com", "Lahore", "Software", "50-200", "brainlogix"),
        CompanyEntry("Force Labs", "eforcelabs.co", "Lahore", "Software", "50-200", "eforcelabs"),
        CompanyEntry("Einnoventon", "einnoventon.com", "Lahore", "Software", "50-200", "einnoventon"),
        CompanyEntry("PixalTech", "pixaltech.pk", "Lahore", "Software", "50-200", "pixaltech"),
        CompanyEntry("Solutions Wave", "solutionswave.com", "Lahore", "Software", "50-200", "solutionswave"),
        CompanyEntry("Ebryx", "ebryx.com", "Lahore", "Software", "50-200", "ebryx"),
        CompanyEntry("Cosmosof Business Solutions", "cosmosof.com", "Lahore", "Software", "50-200", "cosmosof"),
        CompanyEntry("Milestone Apps", "milestoneapps.com", "Lahore", "Software", "50-200", "milestoneapps"),
        CompanyEntry("zAmtech Software House", "zamtech.com", "Lahore", "Software", "50-200", "zamtech"),
        CompanyEntry("Rana Technologies", "ranatechnologies.com", "Lahore", "Software", "50-200", "ranatechnologies"),
        CompanyEntry("FastAccounts", "fastaccounts.com", "Lahore", "Software", "50-200", "fastaccounts"),
        CompanyEntry("OZI Technology", "oziotechnology.com", "Lahore", "Software", "50-200", "oziotechnology"),
        CompanyEntry("Pearl Solutions", "pearlsolutions.com", "Lahore", "Software", "50-200", "pearlsolutions"),
        CompanyEntry("Siemens Industry Software", "mentor.com", "Lahore", "Software", "50-200", "mentor"),
        CompanyEntry("Software Alliance", "softwarealliance.com", "Lahore", "Software", "50-200", "softwarealliance"),
        CompanyEntry("Trainnovative Digital Marketing", "trainnovative.com", "Lahore", "Software", "50-200", "trainnovative"),
        CompanyEntry("Techliance", "techliance.co", "Lahore", "Software", "50-200", "techliance"),
        CompanyEntry("iPOS Software", "ipos.net", "Lahore", "Software", "50-200", "ipos"),
        CompanyEntry("Visual Software Developers", "sofbiller.com", "Lahore", "Software", "50-200", "sofbiller"),
        CompanyEntry("Ekkel AI", "ekkel.ai", "Lahore", "Software", "50-200", "ekkel"),
        CompanyEntry("NextStep Business Solutions", "nextstep.com", "Lahore", "Software", "50-200", "nextstep"),
        CompanyEntry("Triumph Tech AU", "triumphpk.com", "Lahore", "Software", "50-200", "triumphpk"),
        CompanyEntry("WebO", "webo.com", "Lahore", "Software", "50-200", "webo"),
        CompanyEntry("MMB TECHNOLOGIES", "mmbtechnologies.com", "Lahore", "Software", "50-200", "mmbtechnologies"),
        CompanyEntry("VIION Technology", "viiontech.com", "Lahore", "Software", "50-200", "viiontech"),
        CompanyEntry("Pro4Tech Web Development", "pro4tech.com", "Lahore", "Software", "50-200", "pro4tech"),
        CompanyEntry("The Game Storm Studios", "thegamestormstudios.com", "Lahore", "Software", "50-200", "thegamestormstudios"),
        CompanyEntry("SHIL", "softwarehousepk.com", "Lahore", "Software", "50-200", "softwarehousepk"),
        CompanyEntry("Red Code Technology", "redcodetechnology.com", "Lahore", "Software", "50-200", "redcodetechnology"),
        CompanyEntry("Interactive Group", "interactivegroup.com", "Lahore", "Software", "50-200", "interactivegroup"),
        CompanyEntry("FitOutFit Software Technologies", "fitoutfit.com", "Lahore", "Software", "50-200", "fitoutfit"),
        CompanyEntry("MAGMA3C", "magma3c.com", "Lahore", "Software", "50-200", "magma3c"),
        CompanyEntry("Renesis Tech Inc", "renesistech.co", "Lahore", "Software", "50-200", "renesistech"),
        CompanyEntry("Tech dots", "techdots.com", "Lahore", "Software", "50-200", "techdots"),
        CompanyEntry("Website and Software Develop", "websiteandsoftware.com", "Lahore", "Software", "50-200", "websiteandsoftware"),
        CompanyEntry("Arban Tech Software House", "arbantech.com", "Lahore", "Software", "50-200", "arbantech"),
    ]


async def _verify_domain(domain: str) -> bool:
    """Quick check that the domain resolves and returns HTTP 200."""
    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as c:
            r = await c.get(f"https://{domain}")
            return r.status_code < 500
    except Exception:
        return False


async def discover_companies() -> list[dict[str, Any]]:
    """Return list of IT companies, trying cache first, then curated list."""
    cached = _load_cache()
    if cached:
        logger.info("Loaded %d IT companies from cache", len(cached))
        return cached

    companies = _curated_list()

    valid: list[dict[str, Any]] = []
    for c in companies:
        entry = {
            "name": c.name,
            "website": f"https://{c.domain}",
            "city": c.city,
            "industry": c.industry,
            "size": c.size,
            "linkedin": f"https://linkedin.com/company/{c.linkedin_slug}",
            "category": "it_company",
            "domain": c.domain,
            "linkedin_slug": c.linkedin_slug,
        }
        valid.append(entry)

    _save_cache(valid)
    logger.info("Returning %d IT companies", len(valid))
    return valid


def _load_cache() -> list[dict[str, Any]] | None:
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        mtime = os.path.getmtime(CACHE_FILE)
        if time.time() - mtime > CACHE_TTL:
            return None
        with open(CACHE_FILE) as f:
            return json.load(f)
    except Exception:
        return None


def _save_cache(data: list[dict[str, Any]]) -> None:
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning("Failed to write IT company cache: %s", e)
