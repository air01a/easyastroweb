
import { ObservatoryCard } from "../../components/observatory/observatoryCard";
import { TelescopeSumUpCard } from "../../components/observatory/telescopeSumUpCard";
import Button from "../../design-system/buttons/main";
import { useCatalogStore,useWebSocketStore, useObserverStore } from "../../store/store";
import {H1, H2} from "../../design-system/text/titles";
export default function Home() {

  const { catalog } = useCatalogStore()
  const messages = useWebSocketStore((state) => state.messages);
  const isConnected = useWebSocketStore((state) => state.isConnected);
  const connect = useWebSocketStore((state) => state.connect);
  const {observatory, telescope, camera, filterWheel} = useObserverStore();


  const location = observatory.name || 'Observatoire Inconnu';
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

  return (
    <main className="text-white p-6 flex flex-col items-center">
      <H1>🌅 Aujourd’hui à {location}</H1>

      <div className="flex flex-wrap md:flex-wrap gap-6 max-w-4xl w-full">
        {/* Carte Soleil */}
        <div className="flex-1 bg-yellow-500/10 border border-yellow-300 rounded-2xl p-6 shadow-lg backdrop-blur-md w-80">
          <H2>☀️ Le Soleil</H2>
          <p>Lever : {sun.rise}</p>
          <p>Coucher : {sun.set}</p>
          <p>Méridien: {sun.meridian}</p>
        </div>

        {/* Carte Lune */}
        <div className="flex-1 bg-white/10 border border-blue-300 rounded-2xl p-6 shadow-lg backdrop-blur-md w-80">
          <H2>🌕 La Lune</H2>
          <p>Lever : {moon.rise}</p>
          <p>Coucher : {moon.set}</p>
          <p>Illumination : {moon.illumination.toFixed(1)}%</p>
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


        <div className="flex-1 bg-yellow-500/10 border border-yellow-300 rounded-2xl p-6 shadow-lg backdrop-blur-md min-w-80 items-center justify-center">
          <h2 className="text-2xl font-semibold mb-4 text-yellow-300">🎤 Le téléscope</h2>
          {!isConnected ? (

              <div className="flex justify-center"><Button onClick={() =>     connect() }>Connect</Button></div>
          ) : (
            <pre>{JSON.stringify(messages, null, 2)}</pre>
          )}
        </div>


                <div className="flex-1 bg-white/10 border border-blue-300 rounded-2xl p-6 shadow-lg backdrop-blur-md w-80">
          <H2>🏞️ Le Site</H2>
            <ObservatoryCard item={observatory}/>
        </div>

                        <div className="flex-1 bg-yellow-500/10 border border-yellow-300 rounded-2xl p-6 shadow-lg backdrop-blur-md w-80">
          <H2>🎤 Le Telescope</H2>
            <TelescopeSumUpCard telescope={telescope} camera={camera} filterWheel={filterWheel} />
        </div>


      </div>
    </main>
  )
}
