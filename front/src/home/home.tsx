
import { ObservatoryCard } from "../../components/observatory/observatoryCard";
import { TelescopeSumUpCard } from "../../components/observatory/telescopeSumUpCard";
import Button from "../../design-system/buttons/main";
import { useCatalogStore, useObserverStore } from "../../store/store";
import {H1, H2} from "../../design-system/text/titles";
import DeviceStatus from "../../components/observatory/hardware";
import { useEffect, useState } from "react";
import { apiService } from "../../api/api";
import LoadingIndicator from "../../design-system/messages/loadingmessage";
import { useTranslation } from 'react-i18next';

export default function Home() {

  const { catalog } = useCatalogStore()
  //const messages = useWebSocketStore((state) => state.messages);
  const {observatory, telescope, camera, filterWheel, setConnected} = useObserverStore();
  const [hardware, setHardware] = useState<Record<string, string>|null>(null);
  const { t } = useTranslation();

  const location = observatory.name || t('global.unknownObservatory');
  const sun = {
    rise: catalog[0]?.sunrise?.toLocaleString().split(' ')[1] || '',
    set: catalog[0]?.sunset?.toLocaleString().split(' ')[1] || '',
    meridian: catalog[0]?.meridian?.toLocaleString().split(' ')[1] || '',
  }
  //console.log(catalog[0].sunrise?.toLocaleString())
  const moon = {
    rise: catalog[1]?.sunrise?.toLocaleString().split(' ')[1] || '', // Assure-toi que l'index est correct
    set: catalog[1]?.sunset?.toLocaleString().split(' ')[1] || '',
    illumination: catalog[1]?.illumination || 0, // Assure-toi que l'index est correct
    image: catalog[1]?.image||'', // Remplace par le bon chemin
  }

  const fetchHardware = async (rescan=false) => {
      try {
        if (rescan) {
          const connection = await apiService.connectHardWare();
          const nowUtcIso = new Date().toISOString();

          if (connection && connection.telescope_connected && connection.camera_connected) {
            await apiService.setUtcDate(nowUtcIso);
            setConnected(true); 
          }

        } 
        const hardwareData = await apiService.getHardwareName();
        setHardware(hardwareData);
      } catch (error) {
        console.error("Error fetching hardware data:", error);
      }
    };


  useEffect(() => {
    const checkConnection = async () => {
      const isConnected = await apiService.getIsConnected();
      if (isConnected && isConnected.telescope_connected && isConnected.camera_connected) setConnected(true);
    }

    checkConnection();
    fetchHardware();
  },[]);

  return (
    <main className="text-white p-6 flex flex-col items-center">
      <H1>🌅 {t('home.observatoryWelcome', {observatory:location})}</H1>






      <div className="flex flex-wrap md:flex-wrap gap-6 max-w-4xl w-full">
        <div className="flex-1 bg-yellow-500/10 border border-yellow-300 rounded-2xl p-6 shadow-lg backdrop-blur-md min-w-80 items-center justify-center">
          <h2 className="text-2xl font-semibold mb-4 text-yellow-300">⚙️ {t('home.theHardware')}</h2>
            {hardware && <DeviceStatus
              mount_name={hardware.mount_name}
              fw_name={hardware.fw_name}
              focuser_name={hardware.focuser_name}
              camera_name={hardware.camera_name} 
              date={hardware.utc_date}
              location={hardware.telescope_location}
              
            />}
          {!hardware && <LoadingIndicator/>}
          <div className="mt-4 flex items-center justify-center"><Button onClick={()=>{  setHardware(null);fetchHardware(true)}}>{t('global.update')} </Button></div>
        </div>
        
        {/* Carte Soleil */}
        <div className="flex-1 bg-yellow-500/10 border border-yellow-300 rounded-2xl p-6 shadow-lg backdrop-blur-md w-80">
          <H2>☀️ {t('home.theSun')}</H2>
          <p>{t('global.rise')} : {sun.rise}</p>
          <p>{t('global.set')} : {sun.set}</p>
          <p>{t('global.meridian')}: {sun.meridian}</p>
        </div>

        {/* Carte Lune */}
        <div className="flex-1 bg-white/10 border border-blue-300 rounded-2xl p-6 shadow-lg backdrop-blur-md w-80">
          <H2>🌕 {t('home.theMoon')}</H2>
          <p>{t('global.rise')} : {moon.rise}</p>
          <p>{t('global.set')} : {moon.set}</p>
          <p>{t('global.illumination')} : {moon.illumination.toFixed(1)}%</p>
          <div className="mt-4">
            <img
              src={`/catalog/${moon.image}`}
              alt={`Phase lunaire : ${moon.illumination}`}
              width={100}
              height={100}
              className="mx-auto rounded-full shadow"            
            />
          </div>
        </div>




                <div className="flex-1 bg-white/10 border border-blue-300 rounded-2xl p-6 shadow-lg backdrop-blur-md w-80">
          <H2>🏞️ {t('home.theSite')}</H2>
            <ObservatoryCard item={observatory}/>
        </div>

                        <div className="flex-1 bg-yellow-500/10 border border-yellow-300 rounded-2xl p-6 shadow-lg backdrop-blur-md w-80">
          <H2>🎤 {t('home.theScope')}</H2>
            <TelescopeSumUpCard telescope={telescope} camera={camera} filterWheel={filterWheel} />
        </div>


      </div>
    </main>
  )
}
