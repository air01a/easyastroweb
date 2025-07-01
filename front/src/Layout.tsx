import React from 'react';
import { Outlet } from "react-router-dom";
import NavBar from '../design-system/navbar/navbar'; // adapte le chemin si besoin
import Footer from '../design-system/navbar/footer';


// On ne peut plus passer `params.locale`, donc on détecte le locale autrement (par ex. navigateur)
const RootLayout: React.FC = () => {
  const navbarItems = [
    { name: 'Accueil', href: '/', matcher: 'exact' },
    { name: 'Catalog', href: '/catalog' },
    { name: 'Plan', href: '/plan' },
    { name: 'Config', href: '/config' },
  ];

  return (
    <div>
      <div className="font-sans antialiased min-h-screen flex flex-col bg-gradient-to-br from-black to-sky-800 text-white">
        <NavBar menu={navbarItems}/>
        <main className="flex-1 p-4 bg-gradient-to-br from-black-950 to-sky-800 h-full"><Outlet /> </main>
        <Footer/>
      </div>
      
    </div>
  );
};

export default RootLayout;
