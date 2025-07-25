"use client";
import { useEffect, useState } from "react";
import { getSelectedFromCatalog } from "../../lib/astro/catalog/catalog";
import { useCatalogStore, useObserverStore } from "../../store/store";
import type { CatalogItem } from '../../lib/astro/catalog/catalog.type';
import { ObjectPlanificator } from '../../components/plan/objectplanificator';
import type { ImageConfig } from "../../components/plan/plan.type";
import { dateToNumber } from "../../lib/astro/astro-utils";
import  Button  from "../../design-system/buttons/main";
import { apiService } from "../../api/api";
import { useTranslation } from 'react-i18next';
import DarkInfoPanel from '../../components/dark/dark-warning'
import History from "../../components/history/history"

import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';

import type {
  DragEndEvent,
} from '@dnd-kit/core';

import type { PlanType } from '../../types/api.type'

import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import {
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import Spacer from '../../components/plan/spacer';
// Composant wrapper sortable pour chaque ObjectPlanificator
function SortableObjectPlanificator({ 
  id, 
  index, 
  item, 
  sunrise, 
  sunset, 
  startDate,
  initialConfig,
  onUpdate,
  gains,
  expositions
}: {
  id: number;
  index: number;
  item: CatalogItem;
  sunrise: Date;
  sunset: Date;
  startDate: number;
  initialConfig: ImageConfig[];
  gains: number[],
  expositions: number[],
  onUpdate: (index: number, config: ImageConfig[]) => void;
}) {


  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };
  
  return (
    <div 
      ref={setNodeRef} 
      style={{
        ...style,
        position: 'relative',
        border: '1px solid #e2e8f0',
        borderRadius: '8px',
        padding: '8px',
        marginBottom: '8px'
      }}
      {...attributes}
    >
      {/* Poignée de drag */}
      <div 
        {...listeners}
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          bottom: 0,
          width: '16px',
          backgroundColor: '#f1f5f9',
          cursor: 'grab',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderTopLeftRadius: '8px',
          borderBottomLeftRadius: '8px',
          touchAction: 'none'
        }}
        onMouseDown={(e) => e.currentTarget.style.cursor = 'grabbing'}
        onMouseUp={(e) => e.currentTarget.style.cursor = 'grab'}
      >
        <svg width="8" height="20" viewBox="0 0 8 20" fill="none">
          <circle cx="2" cy="4" r="1" fill="#666"/>
          <circle cx="6" cy="4" r="1" fill="#666"/>
          <circle cx="2" cy="10" r="1" fill="#666"/>
          <circle cx="6" cy="10" r="1" fill="#666"/>
          <circle cx="2" cy="16" r="1" fill="#666"/>
          <circle cx="6" cy="16" r="1" fill="#666"/>
        </svg>
      </div>
      
      {/* Contenu avec marge pour la poignée */}
      <div style={{ marginLeft: '24px' }}>
        <ObjectPlanificator 
          index={index} 
          item={item} 
          sunrise={sunrise} 
          sunset={sunset} 
          startDate={startDate}  
          initialConfig={initialConfig}
          gains={gains}
          expositions={expositions}
          onUpdate={onUpdate}
        />
      </div>
    </div>
  );
}

export default function PlanPage({refresh}:{refresh: ()=>void}) {
    const { catalog } = useCatalogStore()
    const [localCatalog, setLocalCatalog] = useState<CatalogItem[]>([]);
    const { sunRise, sunSet, camera } = useObserverStore();
    const [settings, setSettings] = useState<ImageConfig[][]>([]);
    const [ spacer, setSpacer] = useState<number[]>([])
    const [startDates, setStartDates] = useState<{startDate:number, endDate:number}[]>([]);
    const { t } = useTranslation();
    const [defaultGain, setDefaultGain] = useState<number[]>([]);
    const [defaultExpositions, setDefaultExpositions] = useState<number[]>([]);


    useEffect(() => {
      const fetchDarks = async () => {
        try {
          const data = await apiService.getDarkForCamera(camera.id as string);
          let uniqueGains = Array.from(new Set(data.map(d => d.gain))).sort((a, b) => a - b).filter((gain)=> gain!=camera.default_gain as number);
          const  uniqueExpositions = Array.from(new Set(data.map(d => d.exposition))).sort((a, b) => a - b);
          uniqueGains=[camera.default_gain as number,...uniqueGains]
          setDefaultGain(uniqueGains);
          setDefaultExpositions(uniqueExpositions);

        } catch (error) {
          console.error("Erreur lors du chargement des darks :", error);
        } 
      };

      fetchDarks();
    }, []);


    const sensors = useSensors(
        useSensor(PointerSensor),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    const updateSettings = (index: number, config: ImageConfig[]) => {
        const newSettings = [...settings];
        newSettings[index] = config;
        setSettings(newSettings);
    }

    const getDuration = (settings: ImageConfig[]) => {
        if (!settings) return 0;
        let newDuration = 0;
        settings.forEach((item) => newDuration += item.exposureTime * item.imageCount)
        return newDuration /= 3600;
    }

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;
        if (over && active.id !== over.id) {
            const oldIndex = localCatalog.findIndex(item => item.index === active.id);
            const newIndex = localCatalog.findIndex(item => item.index === over.id);

            // Réorganiser le catalogue et les settings en même temps
            const newLocalCatalog = arrayMove(localCatalog, oldIndex, newIndex);
            const newSettings = arrayMove(settings, oldIndex, newIndex);
            
            setLocalCatalog(newLocalCatalog);
            setSettings(newSettings);
        }
    }

    useEffect(() => {
        const getCatalog = async () => {
            const local = (await getSelectedFromCatalog(catalog)).sort((a, b) => {
                if (a.meridian && b.meridian) {
                    return a.meridian.getTime() - b.meridian.getTime();
                } else return 0;
            });

            setLocalCatalog(local);
            setSpacer(new Array(local.length).fill(0));
            setSettings(new Array(local.length).fill([]));
        }

        getCatalog();
    }, [catalog]);

    useEffect(() => {
        let startDate = dateToNumber(sunSet);

        const newStartDates: {startDate: number, endDate: number}[] = [];

        for (let i = 0; i < settings.length; i++) {
            const duration = spacer[i]/3600+getDuration(settings[i]);
            newStartDates[i] = {startDate: (startDate+spacer[i]/3600) % 24, endDate: (startDate + duration+spacer[i]/3600) % 24}
            startDate += duration % 24;
        }
        setStartDates(newStartDates);
    }, [settings])

    const addSpacer = (id: number, value: number) => {
        const newSpacer = [...spacer];
        newSpacer[id] = value;
        setSpacer(newSpacer);
        setSettings([...settings])
    }

    const run = async () => {
      const plan : PlanType[] = [];
      let start=dateToNumber(sunSet);
      settings.forEach((element, index) => {
        start+=spacer[index]/3600;
        element.forEach((capture) =>{
          const expo = capture.exposureTime;
          const nExpo = capture.imageCount;
          const object = localCatalog[index].name;
          const ra = localCatalog[index].ra;
          const dec = localCatalog[index].dec;
          const filter = capture.filter;
          const focus = capture.focus;
          const gain = capture.gain;
          plan.push({
              start,
              expo,
              nExpo,
              ra,
              dec,
              filter,
              object,
              focus,
              gain
          });
          start+=expo*nExpo / 3600;
        });
      });

      await apiService.sendPlans(plan);
      refresh();
    }

    return (
        <div>
            <div className="flex items-center justify-center">
              <DarkInfoPanel />
            </div>
            <DndContext 
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragEnd={handleDragEnd}
            >
                <SortableContext 
                    items={localCatalog.map(item => item.index)}
                    strategy={verticalListSortingStrategy}
                >
                    {localCatalog.map((item, index) => (
                        <div>
                            <Spacer initialValue={0} onUpdate={addSpacer} id={index} />

                            <SortableObjectPlanificator
                                key={item.index}
                                id={item.index}
                                index={index}
                                item={item}
                                sunrise={sunRise}
                                sunset={sunSet}
                                gains={defaultGain}
                                expositions={defaultExpositions}
                                startDate={startDates[index] ? startDates[index].startDate : 14}
                                initialConfig={settings.length>index?settings[index]:[]}
                                onUpdate={updateSettings}
                            />
                        </div>
                    ))}
                </SortableContext>
            </DndContext>
            <div className="flex items-center justify-center"><Button onClick={() => run()}>{t('global.run')}</Button></div>
            <History refreshKey={0}/>
        </div>
    )
}