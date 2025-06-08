
import { useCatalogStore } from "../../store/store";


export default function Home() {

  const { catalog } = useCatalogStore()

  const location = 'Paris'
  const sun = {
    rise: catalog[0]?.sunrise?.toLocaleString().split(' ')[1] || '',
    set: catalog[0]?.sunset?.toLocaleString().split(' ')[1] || '',
    meridian: catalog[0]?.meridian?.toLocaleString().split(' ')[1] || '',
  }
  console.log(catalog[0].sunrise?.toLocaleString())
  const moon = {
    rise: catalog[1]?.sunrise?.toLocaleString().split(' ')[1] || '', // Assure-toi que l'index est correct
    set: catalog[1]?.sunset?.toLocaleString().split(' ')[1] || '',
    illumination: catalog[1]?.illumination || 0, // Assure-toi que l'index est correct
    image: catalog[1].image, // Remplace par le bon chemin
  }

  return (
    <main className="text-white p-6 flex flex-col items-center">
      <h1 className="text-3xl font-bold mb-8">🌅 Aujourd’hui à {location}</h1>

      <div className="flex flex-col md:flex-row gap-6 max-w-4xl w-full">
        {/* Carte Soleil */}
        <div className="flex-1 bg-yellow-500/10 border border-yellow-300 rounded-2xl p-6 shadow-lg backdrop-blur-md">
          <h2 className="text-2xl font-semibold mb-4 text-yellow-300">☀️ Le Soleil</h2>
          <p>Lever : {sun.rise}</p>
          <p>Coucher : {sun.set}</p>
          <p>Méridien: {sun.meridian}</p>
        </div>

        {/* Carte Lune */}
        <div className="flex-1 bg-white/10 border border-blue-300 rounded-2xl p-6 shadow-lg backdrop-blur-md">
          <h2 className="text-2xl font-semibold mb-4 text-blue-200">🌕 La Lune</h2>
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
      </div>
    </main>
  )
}
