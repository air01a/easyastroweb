import React, { useRef, useEffect, useState } from 'react';
import * as THREE from 'three';

const ThreeJsStarMap = () => {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const cameraRef = useRef(null);
  const fileInputRef = useRef(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [dsoShapes, setDsoShapes] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);

  // Données d'exemple d'étoiles brillantes
  const brightStars = [
    { name: "Sirius", ra: 101.287, dec: -16.716, mag: -1.46 },
    { name: "Canopus", ra: 95.988, dec: -52.696, mag: -0.74 },
    { name: "Arcturus", ra: 213.915, dec: 19.182, mag: -0.05 },
    { name: "Vega", ra: 279.234, dec: 38.784, mag: 0.03 },
    { name: "Capella", ra: 79.172, dec: 45.998, mag: 0.08 },
    { name: "Rigel", ra: 78.634, dec: -8.202, mag: 0.13 },
    { name: "Procyon", ra: 114.825, dec: 5.225, mag: 0.34 },
    { name: "Betelgeuse", ra: 88.793, dec: 7.407, mag: 0.42 },
    { name: "Achernar", ra: 24.429, dec: -57.237, mag: 0.46 },
    { name: "Altair", ra: 297.696, dec: 8.868, mag: 0.77 }
  ];

  // Conversion coordonnées célestes vers position 3D sur sphère
  const celestialToCartesian = (ra, dec, radius = 100) => {
    const raRad = (ra * Math.PI) / 180;
    const decRad = (dec * Math.PI) / 180;
    
    const x = radius * Math.cos(decRad) * Math.cos(raRad);
    const y = radius * Math.sin(decRad);
    const z = radius * Math.cos(decRad) * Math.sin(raRad);
    
    return new THREE.Vector3(x, y, z);
  };

  // Taille de l'étoile basée sur la magnitude
  const getStarSize = (magnitude) => {
    return Math.max(0.1, 2 - magnitude * 0.3);
  };

  // Parser le fichier DSO
  const parseDSOFile = (fileContent) => {
    const lines = fileContent.split('\n').filter(line => line.trim());
    const objects = [];
    let currentObject = null;
    let currentPath = [];

    lines.forEach(line => {
      const parts = line.trim().split(/\s+/);
      if (parts.length < 3) return;

      const ra = parseFloat(parts[0]);
      const dec = parseFloat(parts[1]);
      const type = parseInt(parts[2]);
      
      // Si c'est un début de forme (type 0)
      if (type === 0) {
        // Sauvegarder l'objet précédent s'il existe
        if (currentObject && currentPath.length > 0) {
          currentObject.paths.push([...currentPath]);
        }
        
        // Nouveau nom d'objet
        const objectName = parts.length > 4 ? parts[4] : `Object_${ra.toFixed(2)}_${dec.toFixed(2)}`;
        
        // Chercher si l'objet existe déjà
        currentObject = objects.find(obj => obj.name === objectName);
        if (!currentObject) {
          currentObject = {
            name: objectName,
            paths: []
          };
          objects.push(currentObject);
        }
        
        // Commencer un nouveau chemin
        currentPath = [{ ra, dec }];
      }
      // Si c'est une fin de forme (type 1)
      else if (type === 1) {
        currentPath.push({ ra, dec });
        if (currentObject && currentPath.length > 0) {
          currentObject.paths.push([...currentPath]);
          currentPath = [];
        }
      }
      // Si c'est un point normal (type 2)
      else if (type === 2) {
        currentPath.push({ ra, dec });
      }
    });

    // Ajouter le dernier chemin s'il reste quelque chose
    if (currentObject && currentPath.length > 0) {
      currentObject.paths.push([...currentPath]);
    }

    return objects;
  };

  // Créer les formes DSO dans Three.js
  const createDSOShapes = (scene, dsoObjects) => {
    // Supprimer les anciennes formes DSO
    const existingDSO = scene.getObjectByName('dsoShapes');
    if (existingDSO) {
      scene.remove(existingDSO);
    }

    const dsoGroup = new THREE.Group();
    dsoGroup.name = 'dsoShapes';

    dsoObjects.forEach(obj => {
      const objectGroup = new THREE.Group();
      objectGroup.name = obj.name;

      obj.paths.forEach((path, pathIndex) => {
        if (path.length < 2) return;

        // Créer une géométrie de ligne
        const points = path.map(point => 
          celestialToCartesian(point.ra, point.dec, 98)
        );

        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const material = new THREE.LineBasicMaterial({
          color: 0xff6666,
          transparent: true,
          opacity: 0.8,
          linewidth: 2
        });

        const line = new THREE.Line(geometry, material);
        line.userData = {
          objectName: obj.name,
          pathIndex: pathIndex,
          type: 'dso_shape'
        };

        objectGroup.add(line);

        // Ajouter des points aux intersections importantes
        if (pathIndex === 0) {
          const pointGeometry = new THREE.SphereGeometry(0.3, 8, 8);
          const pointMaterial = new THREE.MeshBasicMaterial({
            color: 0xff9999,
            transparent: true,
            opacity: 0.9
          });

          path.forEach((point, index) => {
            if (index % 5 === 0) { // Un point tous les 5 pour ne pas surcharger
              const pointMesh = new THREE.Mesh(pointGeometry, pointMaterial);
              const position = celestialToCartesian(point.ra, point.dec, 98.5);
              pointMesh.position.copy(position);
              pointMesh.userData = {
                objectName: obj.name,
                pointIndex: index,
                type: 'dso_point',
                coordinates: `RA: ${point.ra.toFixed(3)}°, Dec: ${point.dec.toFixed(3)}°`
              };
              objectGroup.add(pointMesh);
            }
          });
        }
      });

      dsoGroup.add(objectGroup);
    });

    scene.add(dsoGroup);
    return dsoGroup;
  };

  // Gestion du fichier uploadé
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setSelectedFile(file.name);
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target.result;
        const objects = parseDSOFile(content);
        setDsoShapes(objects);
        
        // Créer les formes dans la scène si elle existe
        if (sceneRef.current) {
          createDSOShapes(sceneRef.current, objects);
        }
        
        console.log(`Chargé ${objects.length} objets DSO:`, objects.map(o => o.name));
      } catch (error) {
        console.error('Erreur lors du parsing du fichier:', error);
        alert('Erreur lors du chargement du fichier. Vérifiez le format.');
      }
    };
    
    reader.readAsText(file);
  };

  // Exemple de données pour tester sans fichier
  const loadExampleData = () => {
    const exampleData = `83.79330  -4.64113  0 3 NGC1976_lv3
83.77816  -4.65421  2
83.73272  -4.66628  2
83.71253  -4.67433  2
83.70849  -4.67936  2
83.70848  -4.69345  2
83.71858  -4.71559  2
83.70242  -4.74578  2
83.69837  -4.75986  2
83.67413  -4.79407  2
83.67110  -4.80816  2
83.67109  -4.84540  2
83.67916  -4.87861  2
83.69128  -4.89672  2
83.71956  -4.91987  2
83.73875  -4.92390  2
83.75794  -4.91585  2
83.79228  -4.88466  2
83.80339  -4.87862  2
83.82864  -4.90378  2
83.82965  -4.91888  2
83.83470  -4.93095  2
83.86702  -4.94906  2
83.89531  -4.96013  2
83.95996  -4.95912  2
83.99833  -4.92590  2
84.02054  -4.89671  2
84.02155  -4.89067  2
84.00337  -4.87659  2
84.00033  -4.86350  2
83.99326  -4.85847  2
83.97407  -4.85647  2
83.96094  -4.85144  2
83.95084  -4.80716  2
83.96295  -4.80213  2
83.97608  -4.78602  2
83.99627  -4.78300  2
84.01344  -4.77394  2
84.02050  -4.75985  2
84.01747  -4.74676  2
83.99929  -4.73369  2
83.98111  -4.70250  2
83.94577  -4.69747  2
83.90638  -4.67634  2
83.87306  -4.66327  2
83.82864  -4.63811  2
83.80643  -4.63408  2
83.79330  -4.64113  1`;

    const objects = parseDSOFile(exampleData);
    setDsoShapes(objects);
    setSelectedFile('Exemple NGC1976 (M42)');
    
    if (sceneRef.current) {
      createDSOShapes(sceneRef.current, objects);
    }
  };

  useEffect(() => {
    if (!mountRef.current) return;

    // Configuration de la scène
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000011);
    sceneRef.current = scene;

    // Configuration de la caméra
    const camera = new THREE.PerspectiveCamera(
      75, 
      mountRef.current.clientWidth / mountRef.current.clientHeight, 
      0.1, 
      1000
    );
    camera.position.set(0, 0, 0);
    cameraRef.current = camera;

    // Configuration du renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Groupe pour les étoiles
    const starsGroup = new THREE.Group();
    starsGroup.name = 'stars';
    
    // Création des étoiles brillantes
    brightStars.forEach(star => {
      const starGeometry = new THREE.SphereGeometry(getStarSize(star.mag), 8, 8);
      const starMaterial = new THREE.MeshBasicMaterial({ 
        color: star.mag < 0 ? 0xffffaa : 0xffffff,
        transparent: true,
        opacity: Math.max(0.3, 1 - star.mag * 0.2)
      });
      
      const starMesh = new THREE.Mesh(starGeometry, starMaterial);
      const position = celestialToCartesian(star.ra, star.dec);
      starMesh.position.copy(position);
      starMesh.userData = { name: star.name, type: 'star', magnitude: star.mag };
      
      starsGroup.add(starMesh);
      
      // Ajouter un halo pour les étoiles brillantes
      if (star.mag < 1) {
        const glowGeometry = new THREE.SphereGeometry(getStarSize(star.mag) * 2, 8, 8);
        const glowMaterial = new THREE.MeshBasicMaterial({
          color: 0xffffaa,
          transparent: true,
          opacity: 0.2
        });
        const glowMesh = new THREE.Mesh(glowGeometry, glowMaterial);
        glowMesh.position.copy(position);
        starsGroup.add(glowMesh);
      }
    });

    scene.add(starsGroup);

    // Créer les formes DSO si elles existent déjà
    if (dsoShapes.length > 0) {
      createDSOShapes(scene, dsoShapes);
    }

    // Création d'un fond d'étoiles aléatoires
    const starsGeometry = new THREE.BufferGeometry();
    const starCount = 2000;
    const positions = new Float32Array(starCount * 3);
    
    for (let i = 0; i < starCount * 3; i += 3) {
      const radius = 97;
      const phi = Math.random() * Math.PI * 2;
      const theta = Math.random() * Math.PI;
      
      positions[i] = radius * Math.sin(theta) * Math.cos(phi);
      positions[i + 1] = radius * Math.sin(theta) * Math.sin(phi);
      positions[i + 2] = radius * Math.cos(theta);
    }
    
    starsGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const starsMaterial = new THREE.PointsMaterial({ 
      color: 0xffffff, 
      size: 0.3,
      transparent: true,
      opacity: 0.4
    });
    const starField = new THREE.Points(starsGeometry, starsMaterial);
    scene.add(starField);

    // Contrôles de rotation avec la souris
    let isMouseDown = false;
    let mouseX = 0, mouseY = 0;
    let rotationX = 0, rotationY = 0;

    const handleMouseDown = (event) => {
      isMouseDown = true;
      mouseX = event.clientX;
      mouseY = event.clientY;
    };

    const handleMouseUp = () => {
      isMouseDown = false;
    };

    const handleMouseMove = (event) => {
      if (!isMouseDown) return;

      const deltaX = event.clientX - mouseX;
      const deltaY = event.clientY - mouseY;

      rotationY += deltaX * 0.005;
      rotationX += deltaY * 0.005;

      rotationX = Math.max(-Math.PI/2, Math.min(Math.PI/2, rotationX));

      camera.position.x = 0;
      camera.position.y = 0;
      camera.position.z = 0;
      
      camera.rotation.x = rotationX;
      camera.rotation.y = rotationY;

      mouseX = event.clientX;
      mouseY = event.clientY;
    };

    const handleWheel = (event) => {
      const fov = camera.fov + event.deltaY * 0.05;
      camera.fov = Math.max(10, Math.min(120, fov));
      camera.updateProjectionMatrix();
    };

    // Raycasting pour l'interaction
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const handleClick = (event) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(scene.children, true);

      if (intersects.length > 0) {
        const object = intersects[0].object;
        if (object.userData.type === 'dso_point' || object.userData.type === 'dso_shape') {
          console.log('Objet DSO cliqué:', object.userData);
          alert(`Objet: ${object.userData.objectName}\n${object.userData.coordinates || 'Forme DSO'}`);
        } else if (object.userData.type === 'star') {
          console.log('Étoile cliquée:', object.userData);
          alert(`Étoile: ${object.userData.name}\nMagnitude: ${object.userData.magnitude}`);
        }
      }
    };

    renderer.domElement.addEventListener('mousedown', handleMouseDown);
    renderer.domElement.addEventListener('click', handleClick);
    window.addEventListener('mouseup', handleMouseUp);
    window.addEventListener('mousemove', handleMouseMove);
    renderer.domElement.addEventListener('wheel', handleWheel);

    const handleResize = () => {
      if (!mountRef.current) return;
      
      camera.aspect = mountRef.current.clientWidth / mountRef.current.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    };

    window.addEventListener('resize', handleResize);

    const animate = () => {
      requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();

    setIsLoaded(true);

    return () => {
      renderer.domElement.removeEventListener('mousedown', handleMouseDown);
      renderer.domElement.removeEventListener('click', handleClick);
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('mousemove', handleMouseMove);
      renderer.domElement.removeEventListener('wheel', handleWheel);
      window.removeEventListener('resize', handleResize);
      
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  // Mettre à jour les formes DSO quand elles changent
  useEffect(() => {
    if (sceneRef.current && dsoShapes.length > 0) {
      createDSOShapes(sceneRef.current, dsoShapes);
    }
  }, [dsoShapes]);

  return (
    <div className="w-full h-full">
      <div className="mb-4 p-4 bg-gray-100 rounded-lg">
        <h2 className="text-xl font-bold mb-3">Carte du Ciel avec Objets DSO</h2>
        
        {/* Upload de fichier */}
        <div className="mb-4 space-y-2">
          <div className="flex items-center space-x-4">
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.dat"
              onChange={handleFileUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Charger fichier DSO
            </button>
            <button
              onClick={loadExampleData}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
            >
              Charger exemple (NGC1976/M42)
            </button>
          </div>
          {selectedFile && (
            <div className="text-sm text-green-700 bg-green-50 p-2 rounded">
              Fichier chargé: {selectedFile} ({dsoShapes.length} objets)
            </div>
          )}
        </div>

        <div className="text-sm text-gray-600 space-y-1">
          <p><strong>Contrôles :</strong></p>
          <ul className="list-disc list-inside">
            <li>Cliquer-glisser pour faire pivoter</li>
            <li>Molette pour zoomer/dézoomer</li>
            <li>Cliquer sur un objet pour voir ses infos</li>
          </ul>
          <p><strong>Légende :</strong></p>
          <ul className="list-disc list-inside">
            <li><span className="text-white bg-gray-800 px-1 rounded">Blanc/Jaune</span> - Étoiles</li>
            <li><span className="text-red-400">Rouge</span> - Formes DSO (lignes et points)</li>
            <li><span className="text-gray-400">Gris</span> - Fond d'étoiles</li>
          </ul>
          <p><strong>Format fichier :</strong> RA(°) Dec(°) Type [Info] [Nom]</p>
          <p className="text-xs">Type: 0=début, 1=fin, 2=ligne normale</p>
        </div>
      </div>

      <div 
        ref={mountRef} 
        className="w-full bg-black rounded-lg cursor-move"
        style={{ height: '600px' }}
      />

      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 rounded-lg">
          <div className="text-white">Chargement de la carte céleste...</div>
        </div>
      )}
    </div>
  );
};

export default ThreeJsStarMap;