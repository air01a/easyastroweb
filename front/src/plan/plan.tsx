"use client";
import { useEffect, useState } from "react";
import { getSelectedFromCatalog } from "../../lib/astro/catalog/catalog";
import { useCatalogStore, useObserverStore } from "../../store/store";
import type { CatalogItem } from '../../lib/astro/catalog/catalog.type';
import { ObjectPlanificator } from '../../components/plan/objectplanificator';
import type { ImageConfig } from "../../components/plan/plan.type";
import { dateToNumber } from "../../lib/astro/astro-utils";

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

// Composant wrapper sortable pour chaque ObjectPlanificator
function SortableObjectPlanificator({ 
  id, 
  index, 
  item, 
  sunrise, 
  sunset, 
  startDate,
  initialConfig,
  onUpdate 
}: {
  id: number;
  index: number;
  item: CatalogItem;
  sunrise: Date;
  sunset: Date;
  startDate: number;
  initialConfig: ImageConfig[];
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
          onUpdate={onUpdate}
        />
      </div>
    </div>
  );
}

export default function PlanPage() {
    const { catalog } = useCatalogStore()
    const [localCatalog, setLocalCatalog] = useState<CatalogItem[]>([]);
    const { sunRise, sunSet } = useObserverStore();
    const [settings, setSettings] = useState<ImageConfig[][]>([]);
    const [startDates, setStartDates] = useState<{startDate:number, endDate:number}[]>([]);

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
        }

        getCatalog();
    }, [catalog]);

    useEffect(() => {
        let startDate = dateToNumber(sunSet);
        const newStartDates: {startDate: number, endDate: number}[] = [];

        for (let i = 0; i < settings.length; i++) {
            const duration = getDuration(settings[i]);
            newStartDates[i] = {startDate: startDate % 24, endDate: (startDate + duration) % 24}
            startDate += duration % 24;
        }
        setStartDates(newStartDates);
    }, [settings])

    return (
        <div>
            <h1>Plan</h1>
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
                            <div className="flex flex-col justify-center  items-center">➕ Add delay</div>

                            <SortableObjectPlanificator
                                key={item.index}
                                id={item.index}
                                index={index}
                                item={item}
                                sunrise={sunRise}
                                sunset={sunSet}
                                startDate={startDates[index] ? startDates[index].startDate : 14}
                                initialConfig={settings.length>index?settings[index]:[]}
                                onUpdate={updateSettings}
                            />
                        </div>
                    ))}
                </SortableContext>
            </DndContext>
        </div>
    )
}