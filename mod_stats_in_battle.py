__version__= '1.0'
import json, time, urllib2, math, os, re

import BigWorld

from gui.battle_control.arena_info import getClientArena, getArenaGuiType
from account_helpers.settings_core.SettingsCore import g_settingsCore
from gui.Scaleform.daapi.view.battle.stats_form import _StatsForm
from gui.battle_control.battle_arena_ctrl import BattleArenaController
from gui.battle_control.arena_info.ArenaDataProvider import ArenaDataProvider
from gui.Scaleform.Battle import Battle
from gui.Scaleform.daapi.view.battle_loading import BattleLoading
from gui.Scaleform.daapi.view.battle.markers import _VehicleMarker, MarkersManager
from gui import GUI_SETTINGS
from gui.Scaleform import VoiceChatInterface
from gui.battle_control.arena_info.arena_vos import VehicleActions
from gui.battle_control import g_sessionProvider, arena_info
from CTFManager import g_ctfManager

print '[LOAD] mod StatsInBattle v%s' % __version__

class config:
    config={}
    def __init__(self):
        self.loadConfig()
        return
    def loadConfig(self):
        try:
            f=open('res_mods/configs/StatsInBattle/StatsInBattle.json','r')
            self.config=f.read()
            f.close()
        except IOError:
            print '[StatsInBattle] Cannot open config file (res_mods/configs/StatsInBattle/StatsInBattle.json)'
            self.loadDefault()
            #print self.isValidConfig(self.config)
            return
        self.config=json.loads(self.deleteComments(self.config))
        if self.isValidConfig(self.config):
            print '[StatsInBattle] Config successfully loaded.'
        else:
            print '[StatsInBattle] Config is not valid.'
            self.loadDefault()
        return
    def deleteComments(self,data):
        result=''
        j=0
        for i in range(len(data)):
            if data[i]=='/' and data[i+1]=='*':
                j=data.find('*/',i)+2
                if j==-1:
                    j=len(data)
            elif not i<j:
                result+=data[i]
        data=result
        result=''
        j=0
        for i in range(len(data)):
            if data[i]=='/'and data[i+1]=='/':
                j=data.find('\n',i)
                if j==-1:
                    j=len(data)
            elif not i < j:
                result+=data[i]
        return result

    def isValidConfig(self,cfg):
        try:
            cfg['enable']
            cfg['region']
            cfg['disableOnGlobalMap']
            cfg['roundWinrate']
            cfg['playersPanel']['enable']
            cfg['playersPanel']['large']['nick']['left']
            cfg['playersPanel']['large']['nick']['right']
            cfg['playersPanel']['large']['vehicle']['left']
            cfg['playersPanel']['large']['vehicle']['right']
            cfg['playersPanel']['medium2']['left']
            cfg['playersPanel']['medium2']['right']
            cfg['playersPanel']['medium']['left']
            cfg['playersPanel']['medium']['right']
            cfg['tab']['enable']
            cfg['tab']['nick']['left']
            cfg['tab']['nick']['right']
            cfg['tab']['vehicle']['left']
            cfg['tab']['vehicle']['right']
            cfg['battleLoading']['enable']
            cfg['battleLoading']['nick']['left']
            cfg['battleLoading']['nick']['right']
            cfg['battleLoading']['vehicle']['left']
            cfg['battleLoading']['vehicle']['right']
            cfg['marker']['enable']
            cfg['marker']['nick']
            cfg['marker']['vehicle']
            cfg['colors']['colorCodes']
            cfg['colors']['colorEFF']
            cfg['colors']['colorWGR']
            cfg['colors']['colorWinrate']
            cfg['colors']['colorBattles']
            if not len(cfg['colors']['colorCodes'])==len(cfg['colors']['colorEFF'])==len(cfg['colors']['colorWGR'])==len(cfg['colors']['colorWinrate'])==len(cfg['colors']['colorBattles']):
                raise KeyError
            return True
        except KeyError:
            return False


    def loadDefault(self):
        print '[StatsInBattle] Loading default config.'
        self.config={
            'enable': True,
            'region': 'ru',
            'disableOnGlobalMap': True,
            'roundWinrate': 0,
            'playersPanel':{
                'enable': True,
                'large':{
                    'nick':{
                        'left': "<font color='#{colorBattles}'>{kb}</font> <font color='#{default_color}'>{nick}</font><br/>",
                        'right': "<font color='#{default_color}'>{nick}</font> <font color='#{colorBattles}'>{kb}</font><br/>"
                        },
                    'vehicle':{
                        'left': "<font color='#{colorEFF}'>{eff}</font> <font color='#{colorWinrate}'>{winrate}%</font><br/>",
                        'right': "<font color='#{colorWinrate}'>{winrate}%</font> <font color='#{colorEFF}'>{eff}</font><br/>"
                        }
                    },
                'medium2':{
                    'left': "<font color='#{colorEFF}'>{eff}</font> <font color='#{colorWinrate}'>{winrate}%</font><br/>",
                    'right': "<font color='#{colorWinrate}'>{winrate}%</font> <font color='#{colorEFF}'>{eff}</font><br/>"
                    },
                'medium':{
                    'left': "<font color='#{colorEFF}'>{nick}</font><br/>",
                    'right': "<font color='#{colorEFF}'>{nick}</font><br/>"
                    }
            },
            'tab':{
               'enable': True,
               'nick':{
                   'left': "{nick}",
                   'right': "{nick}"
               },
               'vehicle': {
                   'left': "{vehicle} {kb} {winrate}% {eff}",
                   'right': "{eff} {winrate}% {kb} {vehicle}"
               }
            },
            'battleLoading':{
               'enable': True,
               'nick':{
                   'left': "{nick}",
                   'right': "{nick}"
               },
               'vehicle': {
                   'left': "{kb} {winrate}% {eff}",
                   'right': "{eff} {winrate}% {kb}"
               }
            },
            "marker": {
                "enable": True,
                "nick": "{winrate}% {nick}",
                "vehicle": "{eff} {vehicle}"
            },
            'colors':{
                'colorCodes': ['FE0E00','FE7903','F8F400','60FF00','02C9B3','D042F3'],
                'colorEFF': [1,615,870,1175,1525,1850],
                'colorWGR': [1,2495,4345,6425,8625,10040],
                'colorWinrate': [1,47,49,52.5,58,65],
                'colorBattles': [1,2000,6000,16000,30000,43000]
            }
        }
        return

class statistics:
    def __init__(self):
        self.getEncyclopediaTanks()

    def loadStats(self, ids):
        idsStr=','.join(ids)
        self.account_info = 'http://api.worldoftanks.{region}/wot/account/info/?application_id=demo&fields=global_rating%2Cstatistics.all.battles%2Cstatistics.all.wins%2Cstatistics.all.damage_dealt%2Cstatistics.all.frags%2Cstatistics.all.spotted%2Cstatistics.all.capture_points%2Cstatistics.all.dropped_capture_points&account_id={id}'.format(id=idsStr, region=config['region'])
        self.account_tanks = 'http://api.worldoftanks.{region}/wot/account/tanks/?application_id=demo&fields=statistics.battles%2Ctank_id&account_id={id}'.format(id=idsStr, region=config['region'])
        try:
            self.account_info = json.loads(urllib2.urlopen(self.account_info, timeout=30).read()).get('data', None)
            self.account_tanks = json.loads(urllib2.urlopen(self.account_tanks, timeout=30).read()).get('data', None)
        except IOError:
            print '[StatsInBattle] Error stats loading'
            self.stats={}
            return
        self.stats={}
        for uid in ids:
            if self.account_info[uid]['statistics']['all']['battles']!=0:
                self.stats[uid] = {}
                self.stats[uid]['wgr'] = self.account_info[uid]['global_rating']
                self.stats[uid]['battles'] = self.account_info[uid]['statistics']['all']['battles']
                self.stats[uid]['winrate'] = round(self.account_info[uid]['statistics']['all']['wins'] * 100.0 / self.account_info[uid]['statistics']['all']['battles'], config['roundWinrate']) if config['roundWinrate']!=0 else int(round(self.account_info[uid]['statistics']['all']['wins'] * 100.0 / self.account_info[uid]['statistics']['all']['battles'], 0))
                self.stats[uid]['kb'] = str(int(round(self.account_info[uid]['statistics']['all']['battles']/1000,0)))+'k' if self.account_info[uid]['statistics']['all']['battles']>=1000 else self.account_info[uid]['statistics']['all']['battles']
                self.stats[uid]['eff'] = self.getEFF(uid)
                self.stats[uid]['colorWGR'] = self.getColor('colorWGR',self.stats[uid]['wgr'])
                self.stats[uid]['colorBattles'] = self.getColor('colorBattles',self.stats[uid]['battles'])
                self.stats[uid]['colorWinrate'] = self.getColor('colorWinrate',self.stats[uid]['winrate'])
                self.stats[uid]['colorEFF'] = self.getColor('colorEFF',self.stats[uid]['eff'])
        return

    def resetStats(self):
        self.account_info={}
        self.account_tanks={}
        self.stats={}

    def getEFF(self, uid):
        eff_DAMAGE = self.account_info[uid]['statistics']['all']['damage_dealt'] / float(self.account_info[uid]['statistics']['all']['battles'])
        eff_FRAGS = self.account_info[uid]['statistics']['all']['frags'] / float(self.account_info[uid]['statistics']['all']['battles'])
        eff_SPOT = self.account_info[uid]['statistics']['all']['spotted'] / float(self.account_info[uid]['statistics']['all']['battles'])
        eff_CAP = self.account_info[uid]['statistics']['all']['capture_points'] / float(self.account_info[uid]['statistics']['all']['battles'])
        eff_DEF = self.account_info[uid]['statistics']['all']['dropped_capture_points'] / float(self.account_info[uid]['statistics']['all']['battles'])
        player_tier_temp = 0
        try:
            for i in self.account_tanks[uid]:
                player_tier_temp = player_tier_temp + self.encyclopedia_vehicles[str(i['tank_id'])] * i['statistics']['battles']
            eff_TIER = float(player_tier_temp) / self.account_info[uid]['statistics']['all']['battles']
            eff = int(round(eff_DAMAGE * (10 / (eff_TIER + 2)) * (0.23 + 2 * eff_TIER / 100) + eff_FRAGS * 250 + eff_SPOT * 150 + math.log(eff_CAP + 1, 1.732) * 150 + eff_DEF * 150))
        except KeyError as err:
            f=open('res_mods/configs/statsInBattle/missing-vehicles.txt','a')
            f.write('Vehicle id {} missing in encyclopedia. Player with id {} have this vehicle\n'.format(err,uid))
            f.close()
            print '[StatsInBattle] Vehicle id {} missing in encyclopedia. Player with id {} have this vehicle'.format(err,uid)
            eff='err'
        return eff

    def getEncyclopediaTanks(self):
        try:
            f = open('res_mods/configs/statsInBattle/encyclopedia.json','r')
            result = f.read()
            f.close()
            print result
            result=json.loads(result)#).get('data')
            print result
        except Exception:
            request = 'http://api.worldoftanks.ru/wot/encyclopedia/vehicles/?application_id=demo&fields=tier'
            response = json.loads(urllib2.urlopen(request).read()).get('data')
            result={}
            for id in response:
                result[id]=response[id]['tier']
            f = open('res_mods/configs/statsInBattle/encyclopedia.json','w')
            f.write(json.dumps(result))
            f.close()

        result['14353']=7 #Aufklarungspanzer panther
        result['62977']=8 #T-44-100(P)
        self.encyclopedia_vehicles = result
        return

    def getColor(self,rating,value):
        color="FFFFFF"
        if value !='err':
            for i in range(len(config['colors']['colorCodes'])):
                if value>=config['colors'][rating][i]:
                    color=config['colors']['colorCodes'][i]
        return color

def parse(string):
    import re
    try:
        return (re.match("<font color='#(.*?)'>(.*?)</font>", string).group(1), re.match("<font color='#(.*?)'>(.*?)</font>", string).group(2))
    except:
        return ('', '')

def new_ArenaDataProvider_buildVehiclesData(self, vehicles, arenaGuiType):
    old_ArenaDataProvider_buildVehiclesData(self, vehicles, arenaGuiType)
    if ids.count('0') == 0: #Если это не боевое обучение
        stats.loadStats(ids)

def new_ArenaDataProvider_addVehicleInfoVO(self, vID, vInfoVO):
    global ids
    uid = str(vInfoVO.player.accountDBID)
    ids.append(uid)
    return old_ArenaDataProvider_addVehicleInfoVO(self, vID, vInfoVO)

def new_Battle_beforeDelete(self):
    global ids
    old_Battle_beforeDelete(self)
    ids=[]
    stats.resetStats()

def new_Battle_afterCreate(self):
    old_Battle_afterCreate(self)
    ppState = g_settingsCore.getSetting('ppState')
    g_settingsCore.applySetting('ppState', 'none')
    g_settingsCore.applySetting('ppState', ppState)

def new_BattleLoading_makeItem(self, vInfoVO, viStatsVO, userGetter, isSpeaking, actionGetter, regionGetter, playerTeam, isEnemy, squadIdx, isFallout = False):
    dbID = vInfoVO.player.accountDBID
    playerStats = stats.stats.get(str(dbID), None)
    if playerStats is None:
        return old_BattleLoading_makeItem(self, vInfoVO, viStatsVO, userGetter, isSpeaking, actionGetter, regionGetter, playerTeam, isEnemy, squadIdx, isFallout = False)
    makeItem = old_BattleLoading_makeItem(self, vInfoVO, viStatsVO, userGetter, isSpeaking, actionGetter, regionGetter, playerTeam, isEnemy, squadIdx, isFallout = False)
    playerStats['vehicle'] = vInfoVO.vehicleType.shortName
    playerStats['nick'] =  makeItem['playerName']
    makeItem['vehicleGuiName']=(str(config['battleLoading']['vehicle']['left']) if vInfoVO.team == BigWorld.player().team else str(config['battleLoading']['vehicle']['right'])).format(**playerStats)
    makeItem['playerName']=(str(config['battleLoading']['nick']['left']) if vInfoVO.team == BigWorld.player().team else str(config['battleLoading']['nick']['right'])).format(**playerStats)
    return makeItem


def new_StatsForm_getFormattedStrings(self, vInfoVO, vStatsVO, viStatsVO, ctx, fullPlayerName):
    dbID = vInfoVO.player.accountDBID
    playerStats = stats.stats.get(str(dbID), None)
    if getArenaGuiType()==0 and config['disableOnGlobalMap'] == True or playerStats is None:
        return old_StatsFormget_FormattedStrings(self, vInfoVO, vStatsVO, viStatsVO, ctx, fullPlayerName)
    fullPlayerName, fragsString, vehicleName, strings = old_StatsFormget_FormattedStrings(self, vInfoVO, vStatsVO, viStatsVO, ctx, fullPlayerName)
    playerStats['vehicle'] = parse(vehicleName.replace('<br/>', ''))[1]
    playerStats['nick'] = parse(fullPlayerName.replace('<br/>', ''))[1]
    playerStats['default_color'] = parse(vehicleName.replace('<br/>', ''))[0]

    if g_settingsCore.getSetting('ppState') == 'large':
        fullPlayerName = (str(config['playersPanel']['large']['nick']['left']) if vInfoVO.team == BigWorld.player().team else str(config['playersPanel']['large']['nick']['right'])).format(**playerStats)
        vehicleName = (str(config['playersPanel']['large']['vehicle']['left']) if vInfoVO.team == BigWorld.player().team else str(config['playersPanel']['large']['vehicle']['right'])).format(**playerStats)


    if g_settingsCore.getSetting('ppState') == 'medium2':
        vehicleName = (str(config['playersPanel']['medium2']['left']) if vInfoVO.team == BigWorld.player().team else str(config['playersPanel']['medium2']['right'])).format(**playerStats)

    if g_settingsCore.getSetting('ppState') == 'medium':
        fullPlayerName = (str(config['playersPanel']['medium']['left']) if vInfoVO.team == BigWorld.player().team else str(config['playersPanel']['medium2']['right'])).format(**playerStats)
    return (fullPlayerName, fragsString, vehicleName, strings)

def new_BattleArenaController_makeHash(self,index, playerFullName, vInfoVO, vStatsVO, viStatsVO, ctx, playerAccountID, inviteSendingProhibited, invitesReceivingProhibited, isEnemy):
    dbID = vInfoVO.player.accountDBID
    playerStats = stats.stats.get(str(dbID), None)
    if playerStats is None:
        return old_BattleArenaController_makeHash(self, index, playerFullName, vInfoVO, vStatsVO, viStatsVO, ctx, playerAccountID, inviteSendingProhibited, invitesReceivingProhibited, isEnemy)
    makeHash = old_BattleArenaController_makeHash(self, index, playerFullName, vInfoVO, vStatsVO, viStatsVO, ctx, playerAccountID, inviteSendingProhibited, invitesReceivingProhibited, isEnemy)
    playerStats['vehicle']=vInfoVO.vehicleType.shortName
    playerStats['nick']=vInfoVO.player.getPlayerLabel()
    makeHash['vehicle']=(str(config['tab']['vehicle']['left']) if vInfoVO.team == BigWorld.player().team else str(config['tab']['vehicle']['right'])).format(**playerStats)
    makeHash['userName']=(str(config['tab']['nick']['left']) if vInfoVO.team == BigWorld.player().team else str(config['tab']['nick']['right'])).format(**playerStats)
    return makeHash

def new_MarkersManager_addVehicleMarker(self, vProxy, vInfo, guiProps):
    dbID = vInfo.player.accountDBID
    playerStats = stats.stats.get(str(dbID), None)
    if playerStats is None:
        return old_MarkersManager_addVehicleMarker(self, vProxy, vInfo, guiProps)
    #----------- original code ------------------
    vTypeDescr = vProxy.typeDescriptor
    maxHealth = vTypeDescr.maxHealth
    mProv = vProxy.model.node('HP_gui')
    isAlly = guiProps.isFriend
    speaking = False
    if GUI_SETTINGS.voiceChat:
        speaking = VoiceChatInterface.g_instance.isPlayerSpeaking(vInfo.player.accountDBID)
    hunting = VehicleActions.isHunting(vInfo.events)
    markerID = self._MarkersManager__ownUI.addMarker(mProv, 'VehicleMarkerAlly' if isAlly else 'VehicleMarkerEnemy')
    self._MarkersManager__markers[vInfo.vehicleID] = _VehicleMarker(markerID, vProxy, self._MarkersManager__ownUIProxy)
    battleCtx = g_sessionProvider.getCtx()
    fullName, pName, clanAbbrev, regionCode, vehShortName = battleCtx.getFullPlayerNameWithParts(vProxy.id)
    vType = vInfo.vehicleType
    squadIcon = ''
    if arena_info.getIsMultiteam() and vInfo.isSquadMan():
        teamIdx = g_sessionProvider.getArenaDP().getMultiTeamsIndexes()[vInfo.team]
        squadIconTemplate = '%s%d'
        if guiProps.name() == 'squadman':
            squadTeam = 'my'
        elif isAlly:
            squadTeam = 'ally'
        else:
            squadTeam = 'enemy'
        squadIcon = squadIconTemplate % (squadTeam, teamIdx)
    #----- end -------
    playerStats['vehicle']=vehShortName
    playerStats['nick']=pName
    vehShortName = str(config['marker']['vehicle']).format(**playerStats)
    pName = str(config['marker']['nick']).format(**playerStats)
    #----------- original code ------------------
    self.invokeMarker(markerID, 'init', [vType.classTag,
     vType.iconPath,
     vehShortName,
     vType.level,
     fullName,
     pName,
     clanAbbrev,
     regionCode,
     vProxy.health,
     maxHealth,
     guiProps.name(),
     speaking,
     hunting,
     guiProps.base,
     g_ctfManager.isFlagBearer(vInfo.vehicleID),
     squadIcon])
    return markerID
    #----------- end -----------------
def loadMod():
    if config['enable']:
        global stats
        global ids
        global old_ArenaDataProvider_buildVehiclesData
        global old_ArenaDataProvider_addVehicleInfoVO
        global old_Battle_beforeDelete
        global old_Battle_afterCreate
        stats=statistics()
        ids=[]
        old_Battle_afterCreate = Battle.afterCreate
        old_Battle_beforeDelete = Battle.beforeDelete
        old_ArenaDataProvider_buildVehiclesData = ArenaDataProvider.buildVehiclesData
        old_ArenaDataProvider_addVehicleInfoVO = ArenaDataProvider._ArenaDataProvider__addVehicleInfoVO
        Battle.beforeDelete=new_Battle_beforeDelete
        ArenaDataProvider.buildVehiclesData = new_ArenaDataProvider_buildVehiclesData
        ArenaDataProvider._ArenaDataProvider__addVehicleInfoVO = new_ArenaDataProvider_addVehicleInfoVO
        if config['playersPanel']['enable']:
            global old_StatsFormget_FormattedStrings
            old_StatsFormget_FormattedStrings = _StatsForm.getFormattedStrings
            _StatsForm.getFormattedStrings = new_StatsForm_getFormattedStrings
        if config['tab']['enable']:
            global old_BattleArenaController_makeHash
            old_BattleArenaController_makeHash = BattleArenaController._makeHash
            BattleArenaController._makeHash = new_BattleArenaController_makeHash
        if config['battleLoading']['enable']:
            global old_BattleLoading_makeItem
            old_BattleLoading_makeItem = BattleLoading._makeItem
            BattleLoading._makeItem = new_BattleLoading_makeItem
        if config['marker']['enable']:
            global old_MarkersManager_addVehicleMarker
            old_MarkersManager_addVehicleMarker = MarkersManager.addVehicleMarker
            MarkersManager.addVehicleMarker = new_MarkersManager_addVehicleMarker
config=config()
config=config.config
loadMod()
