import time
import threading
import queue
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Callable
import logging
import heapq

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SchedulerStatus(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"

@dataclass
class ObservationTarget:
    """Définit une cible d'observation"""
    name: str
    ra: float  # Ascension droite en heures
    dec: float  # Déclinaison en degrés
    priority: int = 1  # Priorité (1 = haute, 5 = basse)

@dataclass
class ObservationTask:
    """Définit une tâche d'observation"""
    id: str
    target: ObservationTarget
    start_time: datetime
    exposure_time: float  # Temps d'exposition en secondes
    num_exposures: int
    filter_name: Optional[str] = None
    binning: tuple = (1, 1)
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    
    def __post_init__(self):
        if not self.id:
            self.id = f"{self.target.name}_{self.start_time.strftime('%Y%m%d_%H%M%S')}"
            
    def __lt__(self, other):
        """Pour permettre la comparaison dans la priority queue"""
        if self.start_time != other.start_time:
            return self.start_time < other.start_time
        return self.target.priority < other.target.priority

class TelescopeScheduler:
    """Scheduler principal pour les observations télescopiques"""
    
    def __init__(self, ascom_interface):
        self.ascom = ascom_interface  # Votre interface ASCOM
        
        # Utilisation de structures thread-safe
        self.task_queue = queue.PriorityQueue()  # Queue prioritaire pour les tâches
        self.completed_tasks = queue.Queue()     # Queue pour les tâches terminées
        self.all_tasks = {}                      # Dict pour accès rapide par ID (avec lock)
        self.tasks_lock = threading.RLock()      # Lock pour protéger all_tasks
        
        self.status = SchedulerStatus.STOPPED
        self.current_task: Optional[ObservationTask] = None
        self.scheduler_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Callbacks pour les événements
        self.on_task_started: Optional[Callable] = None
        self.on_task_completed: Optional[Callable] = None
        self.on_task_failed: Optional[Callable] = None
        self.on_scheduler_stopped: Optional[Callable] = None
        
        # Configuration
        self.check_interval = 30  # Vérification toutes les 30 secondes
        self.slew_timeout = 300  # Timeout pour le pointage en secondes
        
    def add_task(self, task: ObservationTask):
        """Ajoute une tâche au scheduler de manière thread-safe"""
        with self.tasks_lock:
            self.all_tasks[task.id] = task
            
        # La queue gérera automatiquement la priorité grâce à __lt__
        self.task_queue.put(task)
        logger.info(f"Tâche ajoutée: {task.id}")
        
    def remove_task(self, task_id: str) -> bool:
        """Supprime une tâche du scheduler"""
        with self.tasks_lock:
            if task_id not in self.all_tasks:
                return False
                
            task = self.all_tasks[task_id]
            if task.status == TaskStatus.RUNNING:
                logger.warning(f"Impossible de supprimer la tâche en cours: {task_id}")
                return False
                
            # Marquer comme annulée plutôt que de la supprimer de la queue
            # (plus sûr car la queue pourrait être en cours de traitement)
            task.status = TaskStatus.CANCELLED
            logger.info(f"Tâche marquée comme annulée: {task_id}")
            return True
        
    def start(self):
        """Démarre le scheduler"""
        if self.status == SchedulerStatus.RUNNING:
            logger.warning("Le scheduler est déjà en cours d'exécution")
            return
            
        self.status = SchedulerStatus.RUNNING
        self.stop_event.clear()
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Scheduler démarré")
        
    def stop(self):
        """Arrête le scheduler"""
        if self.status == SchedulerStatus.STOPPED:
            return
            
        self.status = SchedulerStatus.STOPPED
        self.stop_event.set()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=10)
            
        # Marquer la tâche courante comme annulée si nécessaire
        if self.current_task and self.current_task.status == TaskStatus.RUNNING:
            self.current_task.status = TaskStatus.CANCELLED
            
        logger.info("Scheduler arrêté")
        if self.on_scheduler_stopped:
            self.on_scheduler_stopped()
            
    def pause(self):
        """Met en pause le scheduler"""
        if self.status == SchedulerStatus.RUNNING:
            self.status = SchedulerStatus.PAUSED
            logger.info("Scheduler mis en pause")
            
    def resume(self):
        """Reprend le scheduler après une pause"""
        if self.status == SchedulerStatus.PAUSED:
            self.status = SchedulerStatus.RUNNING
            logger.info("Scheduler repris")
            
    def get_next_task(self) -> Optional[ObservationTask]:
        """Trouve la prochaine tâche à exécuter de manière thread-safe"""
        now = datetime.now()
        
        # Chercher dans la queue jusqu'à trouver une tâche valide
        temp_tasks = []
        next_task = None
        
        try:
            while True:
                try:
                    # Récupérer une tâche avec timeout court pour éviter le blocage
                    task = self.task_queue.get(timeout=0.1)
                    
                    # Vérifier si la tâche est encore valide
                    if task.status == TaskStatus.CANCELLED:
                        continue  # Ignorer les tâches annulées
                        
                    if task.status != TaskStatus.PENDING:
                        continue  # Ignorer les tâches déjà traitées
                        
                    # Vérifier si c'est le bon moment
                    if task.start_time <= now:
                        next_task = task
                        break
                    else:
                        # Pas encore le moment, remettre dans la queue
                        temp_tasks.append(task)
                        
                except queue.Empty:
                    break
                    
        finally:
            # Remettre toutes les tâches temporaires dans la queue
            for task in temp_tasks:
                self.task_queue.put(task)
                
        return next_task
        
    def _scheduler_loop(self):
        """Boucle principale du scheduler"""
        logger.info("Boucle du scheduler démarrée")
        
        while not self.stop_event.is_set():
            try:
                if self.status == SchedulerStatus.PAUSED:
                    time.sleep(self.check_interval)
                    continue
                    
                # Cherche la prochaine tâche
                next_task = self.get_next_task()
                
                if next_task:
                    self.current_task = next_task
                    self._execute_task(next_task)
                    self.current_task = None
                else:
                    # Aucune tâche prête, attendre
                    self._wait_for_next_task()
                    
            except Exception as e:
                logger.error(f"Erreur dans la boucle du scheduler: {e}")
                time.sleep(self.check_interval)
                
        logger.info("Boucle du scheduler terminée")
        
    def _execute_task(self, task: ObservationTask):
        """Exécute une tâche d'observation"""
        logger.info(f"Début d'exécution de la tâche: {task.id}")
        task.status = TaskStatus.RUNNING
        task.attempts += 1
        
        if self.on_task_started:
            self.on_task_started(task)
            
        try:
            # 1. Pointer le télescope vers la cible
            logger.info(f"Pointage vers {task.target.name} (RA: {task.target.ra}, DEC: {task.target.dec})")
            if not self._slew_to_target(task.target):
                raise Exception("Échec du pointage")
                
            # 2. Configurer la caméra
            if not self._configure_camera(task):
                raise Exception("Échec de la configuration caméra")
                
            # 3. Prendre les photos
            if not self._take_exposures(task):
                raise Exception("Échec de la prise de vue")
                
            # Tâche terminée avec succès
            task.status = TaskStatus.COMPLETED
            logger.info(f"Tâche terminée avec succès: {task.id}")
            
            if self.on_task_completed:
                self.on_task_completed(task)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la tâche {task.id}: {e}")
            
            if task.attempts < task.max_attempts:
                task.status = TaskStatus.PENDING
                # Reprogrammer la tâche dans 5 minutes
                task.start_time = datetime.now() + timedelta(minutes=5)
                # Remettre dans la queue
                self.task_queue.put(task)
                logger.info(f"Tâche reprogrammée: {task.id} (tentative {task.attempts}/{task.max_attempts})")
            else:
                task.status = TaskStatus.FAILED
                logger.error(f"Tâche échouée définitivement: {task.id}")
                
            if self.on_task_failed:
                self.on_task_failed(task, str(e))
                
    def _slew_to_target(self, target: ObservationTarget) -> bool:
        """Pointe le télescope vers la cible"""
        try:
            # Utiliser votre interface ASCOM pour pointer
            # self.ascom.telescope.SlewToCoordinates(target.ra, target.dec)
            
            # Simulation du pointage
            logger.info(f"Pointage en cours vers {target.name}...")
            time.sleep(2)  # Remplacer par l'attente réelle du pointage
            
            # Vérifier que le pointage est terminé
            # while self.ascom.telescope.Slewing:
            #     if self.stop_event.wait(1):
            #         return False
            
            logger.info("Pointage terminé")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du pointage: {e}")
            return False
            
    def _configure_camera(self, task: ObservationTask) -> bool:
        """Configure la caméra pour la prise de vue"""
        try:
            # Configurer l'exposition, le binning, le filtre, etc.
            # self.ascom.camera.ExposureTime = task.exposure_time
            # self.ascom.camera.BinX, self.ascom.camera.BinY = task.binning
            
            if task.filter_name:
                # self.ascom.filter_wheel.Position = self._get_filter_position(task.filter_name)
                pass
                
            logger.info(f"Caméra configurée: {task.exposure_time}s, binning {task.binning}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration caméra: {e}")
            return False
            
    def _take_exposures(self, task: ObservationTask) -> bool:
        """Prend les expositions"""
        try:
            for i in range(task.num_exposures):
                if self.stop_event.is_set():
                    return False
                    
                logger.info(f"Exposition {i+1}/{task.num_exposures}")
                
                # Démarrer l'exposition
                # self.ascom.camera.StartExposure(task.exposure_time, True)
                
                # Attendre la fin de l'exposition
                # while not self.ascom.camera.ImageReady:
                #     if self.stop_event.wait(1):
                #         return False
                
                # Simulation de l'exposition
                time.sleep(min(task.exposure_time, 5))  # Simulation
                
                # Sauvegarder l'image
                filename = f"{task.target.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i+1:03d}.fits"
                # self.ascom.camera.SaveImage(filename)
                
                logger.info(f"Image sauvegardée: {filename}")
                
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la prise de vue: {e}")
            return False
            
    def _wait_for_next_task(self):
        """Attend la prochaine tâche ou dort"""
        # Regarder s'il y a des tâches en attente dans la queue
        if self.task_queue.empty():
            logger.info("Aucune tâche en attente")
            self.stop_event.wait(self.check_interval)
            return
            
        # Calculer le temps d'attente jusqu'à la prochaine tâche
        # On ne peut pas facilement peek dans une PriorityQueue, donc on utilise un timeout court
        try:
            task = self.task_queue.get(timeout=0.1)
            wait_seconds = (task.start_time - datetime.now()).total_seconds()
            
            # Remettre la tâche dans la queue
            self.task_queue.put(task)
            
            if wait_seconds > 0:
                logger.info(f"Attente de {wait_seconds:.0f} secondes jusqu'à la prochaine tâche")
                self.stop_event.wait(min(wait_seconds, self.check_interval))
            else:
                time.sleep(1)  # Petite pause pour éviter la surcharge CPU
                
        except queue.Empty:
            logger.info("Aucune tâche en attente")
            self.stop_event.wait(self.check_interval)
            
    def get_status_summary(self) -> dict:
        """Retourne un résumé du statut du scheduler de manière thread-safe"""
        with self.tasks_lock:
            all_tasks_list = list(self.all_tasks.values())
            
        return {
            'scheduler_status': self.status.value,
            'current_task': self.current_task.id if self.current_task else None,
            'total_tasks': len(all_tasks_list),
            'pending_tasks': len([t for t in all_tasks_list if t.status == TaskStatus.PENDING]),
            'completed_tasks': len([t for t in all_tasks_list if t.status == TaskStatus.COMPLETED]),
            'failed_tasks': len([t for t in all_tasks_list if t.status == TaskStatus.FAILED]),
            'cancelled_tasks': len([t for t in all_tasks_list if t.status == TaskStatus.CANCELLED]),
            'queue_size': self.task_queue.qsize()
        }
        
    def get_all_tasks(self) -> List[ObservationTask]:
        """Retourne une copie de toutes les tâches de manière thread-safe"""
        with self.tasks_lock:
            return list(self.all_tasks.values())

# Exemple d'utilisation
if __name__ == "__main__":
    # Supposons que vous avez votre interface ASCOM
    # ascom_interface = YourAscomInterface()
    ascom_interface = None  # Placeholder
    
    # Créer le scheduler
    scheduler = TelescopeScheduler(ascom_interface)
    
    # Définir des callbacks
    def on_task_started(task):
        print(f"Tâche démarrée: {task.id}")
        
    def on_task_completed(task):
        print(f"Tâche terminée: {task.id}")
        
    scheduler.on_task_started = on_task_started
    scheduler.on_task_completed = on_task_completed
    
    # Créer quelques tâches d'exemple
    target1 = ObservationTarget("M31", ra=0.712, dec=41.269, priority=1)
    target2 = ObservationTarget("M42", ra=5.588, dec=-5.389, priority=2)
    
    task1 = ObservationTask(
        id="m31_session1",
        target=target1,
        start_time=datetime.now() + timedelta(seconds=10),
        exposure_time=300,
        num_exposures=5,
        filter_name="Luminance"
    )
    
    task2 = ObservationTask(
        id="m42_session1", 
        target=target2,
        start_time=datetime.now() + timedelta(minutes=30),
        exposure_time=180,
        num_exposures=10,
        filter_name="Ha"
    )
    
    # Ajouter les tâches
    scheduler.add_task(task1)
    scheduler.add_task(task2)
    
    # Démarrer le scheduler
    scheduler.start()
    
    try:
        # Laisser tourner pendant un moment
        time.sleep(120)
    except KeyboardInterrupt:
        print("Arrêt demandé par l'utilisateur")
    finally:
        scheduler.stop()