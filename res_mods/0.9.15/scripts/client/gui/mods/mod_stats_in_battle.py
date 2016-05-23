__version__ = '1.5'
__author__ = 'VasyaPRO_2014'
import json, time, urllib2, math, os, re

import BigWorld
import game
import Keys

from Avatar import PlayerAvatar
from Account import PlayerAccount
from gui import SystemMessages
from gui import InputHandler
from gui.app_loader import g_appLoader
from gui.battle_control.arena_info import getClientArena, getArenaGuiType, isFalloutBattle
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
from messenger.gui.Scaleform.BattleEntry import BattleEntry 

print '[LOAD_MOD] StatsInBattle v%s' % __version__

class Config:
    def __init__(self):
        self.load()
        return
    def __call__(self, path):
        path=path.split("/")
        c=self.config
        for x in path:
            c=c[x]
        return c
    def load(self):
        try:
            file=open('res_mods/configs/StatsInBattle/StatsInBattle.json','r')
            f=file.read()
            #delete comments
            while f.count("/*"):
                f=f.replace(f[f.find("/*"):f.find("*/")+2 if f.find("*/")+2 != 1 else len(f)],"")
            while f.count("//"):
                f=f.replace(f[f.find("//"):f.find("\n",f.find("//")) if f.find("\n",f.find("//")) != -1 else len(f)],"")
            cfg=json.loads(f)
            #check on valid
            cfg['enable']
            cfg['reloadKey']
            cfg['region']
            cfg['applicationID']
            cfg['requestTimeout']
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
        except IOError:
            showMessage('[StatsInBattle] Cannot open config file (res_mods/configs/StatsInBattle/StatsInBattle.json)', 'red')
            self.loadDefault()
        except (ValueError, KeyError):
            showMessage('[StatsInBattle] Config is not valid.', 'red')
            self.loadDefault()
        else:
            self.config=cfg
            showMessage('[StatsInBattle] Config successfully loaded.', 'green')
        finally:
            file.close()
        return
    
    def loadDefault(self):
        showMessage('[StatsInBattle] Loading default config.', "gold")
        self.config={
            'enable': True,
            'reloadKey': 'KEY_F9',
            'region': 'ru',
            'applicationID': 'demo',
            'requestTimeout': 5,
            'roundWinrate': 0,
            'playersPanel':{
                'enable': True,
                'large':{
                    'nick':{
                        'left': "<img src='{flag_url}' width='16' height='12'> <font color='#{colorBattles}'>{kb}</font> <font color='#{default_color}'>{nick}</font><br/>",
                        'right': "<font color='#{default_color}'>{nick}</font> <font color='#{colorBattles}'>{kb}</font> <img src='{flag_url}' width='16' height='12'><br/>"
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
                   'left': "<img src='{flag_url}' width='16' height='12'> {nick}",
                   'right': "{nick} <img src='{flag_url}' width='16' height='12'>"
               },
               'vehicle': {
                   'left': "{kb} {winrate}% {eff}",
                   'right': "{eff} {winrate}% {kb}"
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
        self.account_info = 'https://api.worldoftanks.{region}/wot/account/info/?application_id={appId}&fields=client_language%2Cglobal_rating%2Cstatistics.all.battles%2Cstatistics.all.wins%2Cstatistics.all.damage_dealt%2Cstatistics.all.frags%2Cstatistics.all.spotted%2Cstatistics.all.capture_points%2Cstatistics.all.dropped_capture_points&account_id={id}'.format(id=idsStr, region=config('region'), appId=config('applicationID'))
        self.account_tanks = 'https://api.worldoftanks.{region}/wot/account/tanks/?application_id={appId}&fields=statistics.battles%2Ctank_id&account_id={id}'.format(id=idsStr, region=config('region'), appId=config('applicationID'))
        try:
            self.account_info = json.loads(urllib2.urlopen(self.account_info, timeout=config('requestTimeout')).read()).get('data', None)
            self.account_tanks = json.loads(urllib2.urlopen(self.account_tanks, timeout=config('requestTimeout')).read()).get('data', None)
        except IOError:
            showMessage('[StatsInBattle] Error loading statistics.',"red")
        return
    def getStats(self,ids):
        global playersInfo
        for uid in ids:
            if self.account_info[uid] and self.account_info[uid]['statistics']['all']['battles']!=0:
                playersInfo[uid]['wgr'] = self.account_info[uid]['global_rating']
                playersInfo[uid]['battles'] = self.account_info[uid]['statistics']['all']['battles']
                playersInfo[uid]['winrate'] = round(self.account_info[uid]['statistics']['all']['wins'] * 100.0 / self.account_info[uid]['statistics']['all']['battles'], config('roundWinrate')) if config('roundWinrate')!=0 else int(round(self.account_info[uid]['statistics']['all']['wins'] * 100.0 / self.account_info[uid]['statistics']['all']['battles'], 0))
                playersInfo[uid]['kb'] = str(int(round(self.account_info[uid]['statistics']['all']['battles']/1000,0)))+'k' if self.account_info[uid]['statistics']['all']['battles']>=1000 else self.account_info[uid]['statistics']['all']['battles']
                playersInfo[uid]['eff'] = self.getEFF(uid)
                playersInfo[uid]['lang'] = self.account_info[uid]['client_language']
                playersInfo[uid]['colorWGR'] = self.getColor('colorWGR',playersInfo[uid]['wgr'])
                playersInfo[uid]['colorBattles'] = self.getColor('colorBattles',playersInfo[uid]['battles'])
                playersInfo[uid]['colorWinrate'] = self.getColor('colorWinrate',playersInfo[uid]['winrate'])
                playersInfo[uid]['colorEFF'] = self.getColor('colorEFF',playersInfo[uid]['eff'])
                playersInfo[uid]['flag_url'] = 'img://scripts/client/gui/mods/mod_stats_in_battle/flags/'+playersInfo[uid]['lang']+'.png'
        return

    def resetStats(self):
        self.account_info={}
        self.account_tanks={}

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
            f.write('Vehicle: {}. Player: {}\n'.format(err,uid))
            f.close()
            eff='err'
        return eff

    def getEncyclopediaTanks(self):
        try:
            file = open('res_mods/configs/statsInBattle/encyclopedia.json','r')
            result = file.read()
            result = json.loads(result)
        except Exception:
            request = 'https://api.worldoftanks.{region}/wot/encyclopedia/vehicles/?application_id={appId}&fields=tier'.format(region=config('region'),appId=config('applicationID'))
            response = json.loads(urllib2.urlopen(request).read()).get('data')
            result={}
            for id in response:
                result[id]=response[id]['tier']
            file = open('res_mods/configs/statsInBattle/encyclopedia.json','w')
            file.write(json.dumps(result))
        finally:
            file.close()

        result['14353']=7 #Aufklarungspanzer panther
        result['62977']=8 #T-44-100(P)
        result['62993']=7 #VK 45.03
        result['62225']=7 #VK 45.02 (P) Ausf. B7
        result['57089']=7 #T-44-85
        result['63537']=10 #121B
        result['62721']=8 #Kirovets-1
        result['57377']=8 #T25 Pilot Number 1
        result['62529']=9 #Bat.-Chatillon 25 t AP
        result['64017']=8 #leKpz M 41 90 mm
        result['56145']=6 #Sentinel AC IE2/IV
        result['19217']=10 #Grille 15
        result['51809']=3 #Type 98 Ke-Ni Otsu
        result['50961']=8 #leKpz M 41 90 mm GF
        result['57121']=8 #M46 Patton KR
        self.encyclopedia_vehicles = result
        return

    def getColor(self,rating,value):
        color="FFFFFF"
        if value !='err':
            for i in range(len(config('colors/colorCodes'))):
                if value>=config('colors')[rating][i]:
                    color=config('colors/colorCodes')[i]
        return color
def showMessage(text, color='green'):
    if g_appLoader.getDefBattleApp() is not None:
        g_appLoader.getDefBattleApp().call('battle.PlayerMessagesPanel.ShowMessage', [0, text, color])
    elif isinstance(BigWorld.player(), PlayerAccount):
        SystemMessages.pushMessage(text, type=SystemMessages.SM_TYPE.Warning)
    else:
        print text

def inject_handle_key_event(event):
    is_down, key, mods, is_repeat = game.convertKeyEvent(event)
    isInBattle = g_appLoader.getDefBattleApp()
    try:
        global config, ids
        if key is Keys.__getattribute__(config('reloadKey')) and is_down:
            config.load()
            if isInBattle:
                old_ids=ids
                ids=[]
                for pl in getClientArena().vehicles.values():
                    if str(pl['accountDBID'])!='0':
                        ids.append(str(pl['accountDBID']))
                if old_ids!=ids:
                    stats.loadStats(ids)
                stats.getStats(ids)
    except Exception as e:
        print ('error in inject_handle_key_event', e)

InputHandler.g_instance.onKeyDown += inject_handle_key_event
InputHandler.g_instance.onKeyUp += inject_handle_key_event

def parse(string):
    try:
        return (re.match("<font color='#(.*?)'>(.*?)</font>", string).group(1), re.match("<font color='#(.*?)'>(.*?)</font>", string).group(2))
    except:
        return ('', '')

def new_ArenaDataProvider_buildVehiclesData(self, vehicles, arenaGuiType):
    old_ArenaDataProvider_buildVehiclesData(self, vehicles, arenaGuiType)
    stats.loadStats(ids)
    stats.getStats(ids)

def new_ArenaDataProvider_addVehicleInfoVO(self, vID, vInfoVO):
    global ids
    global playersInfo
    vTypeVO=vInfoVO.vehicleType
    uid = str(vInfoVO.player.accountDBID)
    playersInfo[uid]={}
    playersInfo[uid]['team'] = vInfoVO.team
    playersInfo[uid]['vehicle'] = vInfoVO.vehicleType.shortName
    playersInfo[uid]['name'] = vInfoVO.player.name
    playersInfo[uid]['clan'] = "[%s]" % vInfoVO.player.clanAbbrev if vInfoVO.player.clanAbbrev else ""
    playersInfo[uid]['clannb'] = vInfoVO.player.clanAbbrev
    playersInfo[uid]['nick'] = "%s[%s]" % (vInfoVO.player.name, vInfoVO.player.clanAbbrev) if vInfoVO.player.clanAbbrev else vInfoVO.player.name
    if uid!='0':
        ids.append(uid)
    return old_ArenaDataProvider_addVehicleInfoVO(self, vID, vInfoVO)

def new_Battle_beforeDelete(self):
    global ids
    global playersInfo
    old_Battle_beforeDelete(self)
    ids=[]
    playersInfo={}
    stats.resetStats()

def new_BattleLoading_makeItem(self, vInfoVO, viStatsVO, userGetter, isSpeaking, actionGetter, regionGetter, playerTeam, isEnemy, squadIdx, isFallout = False):
    dbID = vInfoVO.player.accountDBID
    playerInfo = playersInfo.get(str(dbID), None)
    if playerInfo.get('battles') is None or isFalloutBattle():
        return old_BattleLoading_makeItem(self, vInfoVO, viStatsVO, userGetter, isSpeaking, actionGetter, regionGetter, playerTeam, isEnemy, squadIdx, isFallout)
    makeItem = old_BattleLoading_makeItem(self, vInfoVO, viStatsVO, userGetter, isSpeaking, actionGetter, regionGetter, playerTeam, isEnemy, squadIdx, isFallout)
    makeItem['clanAbbrev'] = ''
    makeItem['vehicleGuiName']=(str(config('battleLoading/vehicle/left')) if vInfoVO.team == BigWorld.player().team else str(config('battleLoading/vehicle/right'))).format(**playerInfo)
    makeItem['playerName']=(str(config('battleLoading/nick/left')) if vInfoVO.team == BigWorld.player().team else str(config('battleLoading/nick/right'))).format(**playerInfo)
    return makeItem


def new_StatsForm_getFormattedStrings(self, vInfoVO, vStatsVO, viStatsVO, ctx, fullPlayerName):
    dbID = vInfoVO.player.accountDBID
    playerInfo = playersInfo.get(str(dbID), None)
    if playerInfo.get('battles') is None:
        return old_StatsFormget_FormattedStrings(self, vInfoVO, vStatsVO, viStatsVO, ctx, fullPlayerName)
    fullPlayerName, fragsString, vehicleName, strings, formatPanels = old_StatsFormget_FormattedStrings(self, vInfoVO, vStatsVO, viStatsVO, ctx, fullPlayerName)
    playerInfo['default_color'] = parse(vehicleName.replace('<br/>', ''))[0]
    if g_settingsCore.getSetting('ppState') == 'large':
        formatPanels = (str(config('playersPanel/large/nick/left')) if vInfoVO.team == BigWorld.player().team else str(config('playersPanel/large/nick/right'))).format(**playerInfo)
        vehicleName = (str(config('playersPanel/large/vehicle/left')) if vInfoVO.team == BigWorld.player().team else str(config('playersPanel/large/vehicle/right'))).format(**playerInfo)

    if g_settingsCore.getSetting('ppState') == 'medium2':
        vehicleName = (str(config('playersPanel/medium2/left')) if vInfoVO.team == BigWorld.player().team else str(config('playersPanel/medium2/right'))).format(**playerInfo)

    if g_settingsCore.getSetting('ppState') == 'medium':
        formatPanels = (str(config('playersPanel/medium/left')) if vInfoVO.team == BigWorld.player().team else str(config('playersPanel/medium/right'))).format(**playerInfo)
    return (fullPlayerName, fragsString, vehicleName, strings, formatPanels)

def new_BattleArenaController_makeHash(self,index, playerFullName, vInfoVO, vStatsVO, viStatsVO, ctx, playerAccountID, inviteSendingProhibited, invitesReceivingProhibited, isEnemy):
    dbID = vInfoVO.player.accountDBID
    playerInfo = playersInfo.get(str(dbID), None)
    if playerInfo.get('battles') is None:
        return old_BattleArenaController_makeHash(self, index, playerFullName, vInfoVO, vStatsVO, viStatsVO, ctx, playerAccountID, inviteSendingProhibited, invitesReceivingProhibited, isEnemy)
    makeHash = old_BattleArenaController_makeHash(self, index, playerFullName, vInfoVO, vStatsVO, viStatsVO, ctx, playerAccountID, inviteSendingProhibited, invitesReceivingProhibited, isEnemy)
    makeHash['clanAbbrev'] = ''
    makeHash['vehicle']=(str(config('tab/vehicle/left')) if vInfoVO.team == BigWorld.player().team else str(config('tab/vehicle/right'))).format(**playerInfo)
    makeHash['userName']=(str(config('tab/nick/left')) if vInfoVO.team == BigWorld.player().team else str(config('tab/nick/right'))).format(**playerInfo)
    return makeHash

def new_MarkersManager_addVehicleMarker(self, vProxy, vInfo, guiProps):
    dbID = vInfo.player.accountDBID
    playerInfo = playersInfo.get(str(dbID), None)
    if playerInfo.get('battles') is None:
        return old_MarkersManager_addVehicleMarker(self, vProxy, vInfo, guiProps)

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
    result = battleCtx.getPlayerFullNameParts(vProxy.id)
    vType = vInfo.vehicleType
    squadIcon = ''
    if arena_info.isFalloutMultiTeam() and vInfo.isSquadMan():
        teamIdx = g_sessionProvider.getArenaDP().getMultiTeamsIndexes()[vInfo.team]
        squadIconTemplate = '%s%d'
        if guiProps.name() == 'squadman':
            squadTeam = 'my'
        elif isAlly:
            squadTeam = 'ally'
        else:
            squadTeam = 'enemy'
        squadIcon = squadIconTemplate % (squadTeam, teamIdx)
    self.invokeMarker(markerID, 'init', [vType.classTag,
     vType.iconPath,
     str(config('marker/vehicle')).format(**playerInfo), #result.vehicleName
     vType.level,
     result.playerFullName,
     str(config('marker/nick')).format(**playerInfo), #result.playerName
     "", #clanAbbrev
     result.regionCode,
     vProxy.health,
     maxHealth,
     guiProps.name(),
     speaking,
     hunting,
     guiProps.base,
     g_ctfManager.getVehicleCarriedFlagID(vInfo.vehicleID) is not None,
     squadIcon])
    return markerID

def new_BattleEntry_onAddToIgnored(self, _, uid, userName):
    old_BattleEntry_onAddToIgnored(self, _, uid, playersInfo[str(int(uid))]['name'])

def new_BattleEntry_onAddToFriends(self, _, uid, userName):
    old_BattleEntry_onAddToFriends(self, _, uid, playersInfo[str(int(uid))]['name'])

def loadMod():
    if config('enable'):
        global stats,ids,playersInfo,old_ArenaDataProvider_buildVehiclesData,old_ArenaDataProvider_addVehicleInfoVO,old_Battle_beforeDelete,old_BattleEntry_onAddToIgnored,old_BattleEntry_onAddToFriends
        stats=statistics()
        ids=[]
        playersInfo={}
        old_Battle_beforeDelete = Battle.beforeDelete
        old_ArenaDataProvider_buildVehiclesData = ArenaDataProvider.buildVehiclesData
        old_ArenaDataProvider_addVehicleInfoVO = ArenaDataProvider._ArenaDataProvider__addVehicleInfoVO
        old_BattleEntry_onAddToIgnored = BattleEntry._BattleEntry__onAddToIgnored 
        old_BattleEntry_onAddToFriends = BattleEntry._BattleEntry__onAddToFriends
        BattleEntry._BattleEntry__onAddToIgnored = new_BattleEntry_onAddToIgnored 
        BattleEntry._BattleEntry__onAddToFriends = new_BattleEntry_onAddToFriends 
        Battle.beforeDelete=new_Battle_beforeDelete
        ArenaDataProvider.buildVehiclesData = new_ArenaDataProvider_buildVehiclesData
        ArenaDataProvider._ArenaDataProvider__addVehicleInfoVO = new_ArenaDataProvider_addVehicleInfoVO
        if config('playersPanel/enable'):
            global old_StatsFormget_FormattedStrings
            old_StatsFormget_FormattedStrings = _StatsForm.getFormattedStrings
            _StatsForm.getFormattedStrings = new_StatsForm_getFormattedStrings
        if config('tab/enable'):
            global old_BattleArenaController_makeHash
            old_BattleArenaController_makeHash = BattleArenaController._makeHash
            BattleArenaController._makeHash = new_BattleArenaController_makeHash
        if config('battleLoading/enable'):
            global old_BattleLoading_makeItem
            old_BattleLoading_makeItem = BattleLoading._makeItem
            BattleLoading._makeItem = new_BattleLoading_makeItem
        if config('marker/enable'):
            global old_MarkersManager_addVehicleMarker
            old_MarkersManager_addVehicleMarker = MarkersManager.addVehicleMarker
            MarkersManager.addVehicleMarker = new_MarkersManager_addVehicleMarker
config=Config()
loadMod()