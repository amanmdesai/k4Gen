# FLARE variant: event count read from the card, status-1 filtering in the converter.
import os
import sys
from GaudiKernel import SystemOfUnits as units
from Gaudi.Configuration import *


def _cli_override(flag, argv, default=None):
    for i, token in enumerate(argv):
        if token == flag and i + 1 < len(argv):
            return argv[i + 1]
        if token.startswith(flag + "="):
            return token.split("=", 1)[1]
    return default


def read_num_events_from_card(card_path, default=2):
    try:
        with open(card_path) as f:
            for line in f:
                line = line.split("!", 1)[0].strip()
                if line.lower().startswith("main:numberofevents"):
                    return int(line.split("=", 1)[1].strip())
    except (OSError, ValueError, IndexError):
        pass
    return default


from Configurables import ApplicationMgr
ApplicationMgr().EvtSel = 'NONE'
ApplicationMgr().OutputLevel = INFO
ApplicationMgr().ExtSvc +=["RndmGenSvc"]

#### Data service
from Configurables import k4DataSvc
podioevent = k4DataSvc("EventDataSvc")
ApplicationMgr().ExtSvc += [podioevent]

from Configurables import GaussSmearVertex
smeartool = GaussSmearVertex()
smeartool.xVertexSigma =   0.5*units.mm
smeartool.yVertexSigma =   0.5*units.mm
smeartool.zVertexSigma =  40.0*units.mm
smeartool.tVertexSigma = 180.0*units.picosecond

from Configurables import PythiaInterface
pythia8gentool = PythiaInterface()
### Example of pythia configuration file to generate events
# take from $K4GEN if defined, locally if not
path_to_pythiafile = os.environ.get("K4GEN", "")
pythiafilename = "Pythia_standard.cmd"
pythiafile = os.path.join(path_to_pythiafile, pythiafilename)
# Example of pythia configuration file to read LH event file
#pythiafile="options/Pythia_LHEinput.cmd"
pythiafile = _cli_override(
    "--Pythia8.PythiaInterface.pythiacard", sys.argv, default=pythiafile
)
ApplicationMgr().EvtMax = read_num_events_from_card(pythiafile)
pythia8gentool.pythiacard = pythiafile
pythia8gentool.doEvtGenDecays = False
pythia8gentool.printPythiaStatistics = True
pythia8gentool.pythiaExtraSettings = [""]

from Configurables import GenAlg
pythia8gen = GenAlg("Pythia8")
pythia8gen.SignalProvider = pythia8gentool
pythia8gen.VertexSmearingTool = smeartool
pythia8gen.hepmc.Path = "hepmc"
ApplicationMgr().TopAlg += [pythia8gen]

from Configurables import HepMCToEDMConverter
hepmc_converter = HepMCToEDMConverter()
hepmc_converter.hepmc.Path="hepmc"
hepmc_converter.hepmcStatusList = [1] # only convert final-state (stable) particles
hepmc_converter.GenParticles.Path="MCParticles"
ApplicationMgr().TopAlg += [hepmc_converter]

from Configurables import PodioOutput
out = PodioOutput("out")
out.outputCommands = ["keep *"]
ApplicationMgr().TopAlg += [out]
