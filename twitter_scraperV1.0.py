import time
import csv
import re
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains

class TwitterScraper:
    def __init__(self, headless=False):
        """Inicializar el scraper de Twitter/X."""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")  # Modo headless más reciente
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-automation")  # Evitar detección de automatización
        
        # Configuraciones para evitar detección
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)
        self.actions = ActionChains(self.driver)
        
    def __del__(self):
        """Cerrar el navegador cuando se destruye el objeto."""
        try:
            self.driver.quit()
        except:
            pass
    
    def scroll_down(self, num_scrolls=5, pause=2):
        """Desplazar hacia abajo para cargar más tweets."""
        for i in range(num_scrolls):
            print(f"Scroll {i+1}/{num_scrolls}")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(pause * 0.8, pause * 1.2))  # Pausa aleatoria
    
    def extract_stat_direct(self, tweet, data_testid):
        """Extraer estadística directamente usando data-testid."""
        try:
            # Intentar encontrar el elemento específico por data-testid
            group_element = tweet.find_element(By.CSS_SELECTOR, f'[data-testid="{data_testid}"]')
            
            # En Twitter/X, el texto con el número está en un span dentro del elemento con data-testid
            # o podría estar en el aria-label del elemento padre
            try:
                # Intentar obtener del aria-label
                parent = group_element.find_element(By.XPATH, './..')
                aria_label = parent.get_attribute('aria-label')
                if aria_label:
                    print(f"Aria-label encontrado para {data_testid}: {aria_label}")
                    return extract_number(aria_label)
                
                # Si no hay aria-label, intentar obtener del texto
                span_text = group_element.find_element(By.CSS_SELECTOR, 'span:not([dir])').text
                if span_text:
                    print(f"Texto encontrado para {data_testid}: {span_text}")
                    return extract_number(span_text)
                
                return 0
            except Exception as e:
                print(f"Error al extraer texto para {data_testid}: {e}")
                return 0

        except NoSuchElementException:
            print(f"No se encontró elemento para {data_testid}")
            return 0
        except Exception as e:
            print(f"Error general al buscar {data_testid}: {e}")
            return 0
    
    def extract_tweet_stats(self, tweet):
        """Extraer estadísticas de un tweet (me gusta, comentarios, retweets)."""
        stats = {
            'comentarios': 0,
            'retweets': 0,
            'me_gusta': 0,
            'compartidos': 0
        }
        
        # Asegurarnos de que el tweet es visible
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tweet)
        time.sleep(0.5)
        
        try:
            # Método 1: Buscar directamente por data-testid
            data_testids = {
                'reply': 'comentarios',
                'retweet': 'retweets',
                'like': 'me_gusta',
                'bookmark': 'compartidos'
            }
            
            for testid, stat_key in data_testids.items():
                value = self.extract_stat_direct(tweet, testid)
                if value > 0:  # Solo actualizar si encontramos un valor positivo
                    stats[stat_key] = value
                    
            # Si no encontramos nada, intentamos el método alternativo
            if all(v == 0 for v in stats.values()):
                print("Intentando método alternativo para extraer estadísticas...")
                
                # Método 2: Buscar todos los elementos con role="button" dentro de groups
                metrics_groups = tweet.find_elements(By.CSS_SELECTOR, '[role="group"] [role="button"]')
                for metric in metrics_groups:
                    try:
                        # Obtener el texto y el aria-label
                        aria_text = metric.get_attribute('aria-label') or ""
                        inner_text = metric.text or ""
                        
                        # Usar el texto que tenga información
                        metric_text = aria_text if len(aria_text) > len(inner_text) else inner_text
                        metric_text = metric_text.lower()
                        
                        print(f"Texto de métrica encontrado: {metric_text}")
                        
                        # Check que tipo de métrica es
                        if any(keyword in metric_text for keyword in ["repl", "respuesta", "comment"]):
                            stats['comentarios'] = extract_number(metric_text)
                        elif any(keyword in metric_text for keyword in ["retweet", "retuit"]):
                            stats['retweets'] = extract_number(metric_text)
                        elif any(keyword in metric_text for keyword in ["like", "me gusta"]):
                            stats['me_gusta'] = extract_number(metric_text)
                        elif any(keyword in metric_text for keyword in ["bookmark", "guardar", "compartir"]):
                            stats['compartidos'] = extract_number(metric_text)
                    except StaleElementReferenceException:
                        print("Elemento ya no está disponible (stale)")
                        continue
                    except Exception as e:
                        print(f"Error al procesar métrica: {e}")
                        continue
            
            # Método 3: Si aún tenemos ceros, intentemos extraer números directamente
            if all(v == 0 for v in stats.values()):
                print("Intentando extraer números directamente del tweet...")
                all_spans = tweet.find_elements(By.CSS_SELECTOR, 'span')
                for span in all_spans:
                    try:
                        span_text = span.text.strip()
                        if span_text and re.match(r'^\d+$', span_text):  # Solo números
                            # Intentar determinar el tipo de métrica por su posición o contexto
                            parent = span.find_element(By.XPATH, './..')
                            grandparent = parent.find_element(By.XPATH, './..')
                            
                            # Verificar si hay iconos cercanos que indiquen el tipo
                            if "comment" in grandparent.get_attribute('outerHTML'):
                                stats['comentarios'] = int(span_text)
                            elif "retweet" in grandparent.get_attribute('outerHTML'):
                                stats['retweets'] = int(span_text)
                            elif "like" in grandparent.get_attribute('outerHTML'):
                                stats['me_gusta'] = int(span_text)
                            elif "bookmark" in grandparent.get_attribute('outerHTML'):
                                stats['compartidos'] = int(span_text)
                    except:
                        continue
                
        except Exception as e:
            print(f"Error general al extraer estadísticas: {e}")

        print(f"Estadísticas finales extraídas: {stats}")
        return stats
    
    def extract_tweet_content(self, tweet):
        """Extraer el contenido del tweet."""
        try:
            tweet_text_element = tweet.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
            return tweet_text_element.text
        except NoSuchElementException:
            # Intentar selectores alternativos
            selectors = ['div[lang]', 'div[dir="auto"]']
            for selector in selectors:
                try:
                    elements = tweet.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.text and len(element.text) > 5:  # Probablemente sea el texto del tweet
                            return element.text
                except:
                    continue
            return ""
        except:
            return ""

    def extract_tweet_date(self, tweet):
        """Extraer la fecha del tweet."""
        try:
            time_element = tweet.find_element(By.TAG_NAME, "time")
            return time_element.get_attribute("datetime")
        except:
            return ""
    
    def extract_tweet_url(self, tweet):
        """Extraer la URL del tweet."""
        try:
            # Buscar enlaces que contengan "/status/" en su URL
            link_element = tweet.find_element(By.CSS_SELECTOR, 'a[href*="/status/"]')
            return link_element.get_attribute("href")
        except:
            # Método alternativo: buscar el timestamp que suele ser un enlace al tweet
            try:
                time_link = tweet.find_element(By.CSS_SELECTOR, 'time').find_element(By.XPATH, './..')
                if time_link.tag_name == 'a':
                    return time_link.get_attribute("href")
            except:
                pass
            return ""
    
    def has_media(self, tweet):
        """Verificar si el tweet tiene imágenes o videos."""
        try:
            media_elements = tweet.find_elements(By.CSS_SELECTOR, '[data-testid="tweetPhoto"], video')
            return len(media_elements) > 0
        except:
            return False
            
    def scrape_account(self, account_url, num_tweets=20):
        """Raspar tweets de una cuenta específica de Twitter/X."""
        self.driver.get(account_url)
        print(f"Accediendo a: {account_url}")
        
        # Esperar a que cargue la página
        selectors = ['[data-testid="tweet"]', 'article', '[data-testid="cellInnerDiv"]']
        found = False
        
        for selector in selectors:
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                print(f"Página cargada, encontrado selector: {selector}")
                found = True
                break
            except TimeoutException:
                continue
                
        if not found:
            print("No se pudo cargar la página correctamente")
            return []
        
        # Scroll para cargar más tweets
        num_scrolls_needed = max(2, num_tweets // 4)  # Más scrolls para asegurar cargar suficientes tweets
        self.scroll_down(num_scrolls_needed, pause=3)
        
        # Recolectar tweets con diferentes selectores
        tweet_elements = []
        selectors = [
            '[data-testid="tweet"]',
            'article',
            '[data-testid="cellInnerDiv"] div[data-testid]'
        ]
        
        for selector in selectors:
            tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if len(tweet_elements) > 0:
                print(f"Encontrados {len(tweet_elements)} tweets con selector: {selector}")
                break
        
        if not tweet_elements:
            print("No se encontraron tweets con ninguno de los selectores")
            return []
        
        # Filtrar tweets que parezcan promocionados o repetidos
        filtered_tweets = []
        tweet_urls = set()
        
        for tweet in tweet_elements:
            try:
                url = self.extract_tweet_url(tweet)
                if url and url not in tweet_urls:
                    tweet_urls.add(url)
                    filtered_tweets.append(tweet)
            except:
                continue
                
        print(f"Después de filtrar: {len(filtered_tweets)} tweets únicos")
        
        # Extraer datos de los tweets
        tweets_data = []
        account_handle = account_url.split('/')[-1]
        
        for i, tweet in enumerate(filtered_tweets[:num_tweets]):
            try:
                # Hacer scroll al tweet para asegurar que está en la vista
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tweet)
                time.sleep(1)  # Esperar a que se carguen los contadores
                
                # Intentar extraer datos
                tweet_text = self.extract_tweet_content(tweet)
                tweet_url = self.extract_tweet_url(tweet)
                tweet_date = self.extract_tweet_date(tweet)
                
                tweet_data = {
                    'cuenta': account_handle,
                    'texto': tweet_text,
                    'fecha': tweet_date,
                    'url': tweet_url,
                    'tiene_media': self.has_media(tweet)
                }
                
                # Extraer estadísticas (intentar múltiples veces si es necesario)
                max_attempts = 3
                for attempt in range(max_attempts):
                    stats = self.extract_tweet_stats(tweet)
                    if any(v > 0 for v in stats.values()):  # Si encontramos al menos una métrica
                        break
                    elif attempt < max_attempts - 1:
                        print(f"Reintentando extracción de métricas (intento {attempt+1}/{max_attempts})")
                        time.sleep(1)  # Esperar un poco antes de reintentar
                        
                tweet_data.update(stats)
                
                # Solo agregar tweets con texto o URL válida
                if tweet_text or tweet_url:
                    tweets_data.append(tweet_data)
                    print(f"Tweet {i+1} extraído: {tweet_text[:30]}..." if tweet_text else "Sin texto")
                
            except StaleElementReferenceException:
                print(f"Error: Elemento ya no disponible (stale) para tweet {i+1}")
                continue
            except Exception as e:
                print(f"Error general al extraer tweet {i+1}: {e}")
                continue
        
        return tweets_data
    
    def scrape_multiple_accounts(self, account_urls, output_file='tweets_data.csv', num_tweets_per_account=20):
        """Raspar múltiples cuentas de Twitter/X y guardar los resultados en un CSV."""
        all_tweets = []
        
        for url in account_urls:
            print(f"\n{'='*50}\nRaspando cuenta: {url}\n{'='*50}")
            tweets = self.scrape_account(url, num_tweets_per_account)
            all_tweets.extend(tweets)
            # Pausa entre cuentas para evitar detección
            time.sleep(random.uniform(5, 8))
        
        # Guardar resultados en CSV
        if all_tweets:
            fieldnames = ['cuenta', 'texto', 'fecha', 'url', 'comentarios', 'retweets', 'me_gusta', 'compartidos', 'tiene_media']
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_tweets)
            
            print(f"\nDatos guardados en {output_file}")
            print(f"Total de tweets recolectados: {len(all_tweets)}")
            
            # Mostrar estadísticas por cuenta
            accounts = {}
            for tweet in all_tweets:
                account = tweet['cuenta']
                if account not in accounts:
                    accounts[account] = 0
                accounts[account] += 1
                
            print("\nTweets por cuenta:")
            for account, count in accounts.items():
                print(f"- {account}: {count} tweets")
                
            # Mostrar ejemplos de métricas
            print("\nEjemplos de métricas encontradas:")
            metrics_examples = []
            for tweet in all_tweets:
                if any(tweet[metric] > 0 for metric in ['comentarios', 'retweets', 'me_gusta', 'compartidos']):
                    metrics_examples.append(tweet)
                    if len(metrics_examples) >= 3:
                        break
                        
            for i, example in enumerate(metrics_examples):
                print(f"\nEjemplo {i+1}:")
                print(f"Texto: {example['texto'][:50]}...")
                print(f"Comentarios: {example['comentarios']}")
                print(f"Retweets: {example['retweets']}")
                print(f"Me gusta: {example['me_gusta']}")
                print(f"Compartidos: {example['compartidos']}")
        else:
            print("No se pudieron extraer tweets.")

def extract_number(text):
    """Extraer número de texto como '5 respuestas' o '10.2K Me gusta'."""
    if not text:
        return 0
        
    # Primero, intentemos encontrar patrones comunes de Twitter con K/M
    k_pattern = re.search(r'(\d+(?:[.,]\d+)?)[kK]', text)
    m_pattern = re.search(r'(\d+(?:[.,]\d+)?)[mM]', text)
    
    if k_pattern:
        return int(float(k_pattern.group(1).replace(',', '.')) * 1000)
    if m_pattern:
        return int(float(m_pattern.group(1).replace(',', '.')) * 1000000)
    
    # Buscar patrones como "mil" o "millones"
    if 'mil' in text.lower():
        mil_pattern = re.search(r'(\d+(?:[.,]\d+)?)\s*mil', text.lower())
        if mil_pattern:
            return int(float(mil_pattern.group(1).replace(',', '.')) * 1000)
    
    if 'millon' in text.lower() or 'millones' in text.lower():
        mill_pattern = re.search(r'(\d+(?:[.,]\d+)?)\s*millon(?:es)?', text.lower())
        if mill_pattern:
            return int(float(mill_pattern.group(1).replace(',', '.')) * 1000000)
    
    # Finalmente, buscar cualquier número
    number_pattern = re.search(r'(\d+(?:[.,]\d+)?)', text)
    if number_pattern:
        # Manejar delimitadores decimales
        return int(float(number_pattern.group(1).replace(',', '.')))
    
    return 0

# Ejemplo de uso
if __name__ == "__main__":
    # Lista de cuentas a raspar
    accounts = [
        "https://x.com/BeatlesEarth",
        "https://x.com/cervezaindio",
        "https://x.com/Hasbro"
    ]
    
    # Iniciar el scraper (False para ver el navegador, True para modo headless)
    scraper = TwitterScraper(headless=False)
    
    try:
        # Raspar 20 tweets por cuenta
        scraper.scrape_multiple_accounts(accounts, 'fast_food_tweets.csv', 20)
    finally:
        # Asegurar que el navegador se cierre correctamente
        del scraper