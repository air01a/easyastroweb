"use client";
import { useEffect } from 'react'
import { useCatalogStore, useObserverStore } from '@/store/store'
import { useRouter, usePathname } from 'next/navigation'

export function StoreInitializer() {
  const loadCatalog = useCatalogStore((s) => s.loadCatalog)
  const { isLoaded } = useObserverStore()
  const pathname = usePathname()
  const router = useRouter()



  useEffect(() => {
    
    loadCatalog();
    if (!isLoaded &&  pathname !== '/location') {
      router.replace('/location')

    }
  }, [])

  return null // ce composant ne rend rien
}