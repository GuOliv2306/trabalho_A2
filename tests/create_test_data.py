"""
Script para criar dados de teste no banco DuckDB.
ATENÇÃO: Execute cleanup_test_data.py depois para limpar!
"""

import sys
from pathlib import Path
import random
from datetime import datetime, timedelta

# Adiciona src ao path
sys.path.append(str(Path(__file__).parent.parent))

from src.collectors.db_storage import GA4DatabaseStorage


def generate_test_data():
    """Gera dados de teste realistas para todas as tabelas."""
    db = GA4DatabaseStorage()
    
    print("🔄 Gerando dados de teste...")
    
    # Data base para os testes
    base_date = datetime.now() - timedelta(days=7)
    
    # Lista de páginas de exemplo
    pages = [
        "/produtos/notebook-dell",
        "/produtos/mouse-logitech",
        "/produtos/teclado-mecanico",
        "/blog/como-escolher-notebook",
        "/blog/review-mouse-gamer",
        "/sobre-nos",
        "/contato",
        "/produtos/monitor-lg",
        "/blog/guia-ergonomia",
        "/produtos/cadeira-gamer"
    ]
    
    # 1. Inserir dados de TRAFFIC
    print("  → Inserindo dados de tráfego...")
    traffic_data = []
    property_id = "123456789"  # ID fictício
    
    sources = ['google', 'direct', 'facebook', 'instagram', 'twitter']
    mediums = ['organic', 'cpc', 'referral', 'none', 'email']
    campaigns = ['campaign_a', 'campaign_b', 'summer_sale', '(not set)', 'black_friday']
    
    for source in sources[:3]:  # Só 3 fontes para não criar muitos registros
        for medium in mediums[:3]:
            for day_offset in range(7):
                date = base_date + timedelta(days=day_offset)
                sessions = random.randint(50, 500)
                traffic_data.append({
                    'property_id': property_id,
                    'date': date.strftime('%Y-%m-%d'),
                    'session_source': source,
                    'session_medium': medium,
                    'session_campaign_name': random.choice(campaigns),
                    'sessions': sessions,
                    'active_users': int(sessions * 0.8),
                    'new_users': int(sessions * 0.6),
                    'screen_page_views': int(sessions * random.uniform(1.2, 2.5)),
                    'average_session_duration': round(random.uniform(60, 300), 2),
                    'collected_at': datetime.now().isoformat()
                })
    
    for idx, data in enumerate(traffic_data, start=1):
        db.conn.execute("""
            INSERT INTO traffic (id, property_id, date, session_source, session_medium, 
                               session_campaign_name, sessions, active_users, new_users, 
                               screen_page_views, average_session_duration, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            idx, data['property_id'], data['date'], data['session_source'], data['session_medium'],
            data['session_campaign_name'], data['sessions'], data['active_users'],
            data['new_users'], data['screen_page_views'], data['average_session_duration'],
            data['collected_at']
        ])
    
    print(f"  ✓ {len(traffic_data)} registros de tráfego inseridos")
    
    # 2. Inserir dados de ENGAGEMENT
    print("  → Inserindo dados de engajamento...")
    engagement_data = []
    devices = ['desktop', 'mobile', 'tablet']
    
    for page in pages:
        for device in devices:
            for day_offset in range(7):
                date = base_date + timedelta(days=day_offset)
                sessions = random.randint(50, 500)
                
                # Páginas de blog têm maior engajamento
                is_blog = '/blog/' in page
                engagement_rate = random.uniform(0.5, 0.7) if is_blog else random.uniform(0.2, 0.5)
                avg_duration = random.uniform(200, 450) if is_blog else random.uniform(60, 180)
                
                engagement_data.append({
                    'property_id': property_id,
                    'date': date.strftime('%Y-%m-%d'),
                    'page_path': page,
                    'unified_screen_name': page.replace('/', '_'),
                    'device_category': device,
                    'engagement_rate': round(engagement_rate, 2),
                    'engaged_sessions': int(sessions * engagement_rate),
                    'average_session_duration': round(avg_duration, 1),
                    'event_count': int(sessions * random.uniform(3, 12)),
                    'user_engagement_duration': int(avg_duration * sessions),
                    'collected_at': datetime.now().isoformat()
                })
    
    for idx, data in enumerate(engagement_data, start=1):
        db.conn.execute("""
            INSERT INTO engagement (id, property_id, date, page_path, unified_screen_name,
                                  device_category, engagement_rate, engaged_sessions,
                                  average_session_duration, event_count, user_engagement_duration,
                                  collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            idx, data['property_id'], data['date'], data['page_path'], data['unified_screen_name'],
            data['device_category'], data['engagement_rate'], data['engaged_sessions'],
            data['average_session_duration'], data['event_count'], data['user_engagement_duration'],
            data['collected_at']
        ])
    
    print(f"  ✓ {len(engagement_data)} registros de engajamento inseridos")
    
    # 3. Inserir dados de CONVERSIONS
    print("  → Inserindo dados de conversões...")
    conversion_data = []
    event_names = ['purchase', 'add_to_cart', 'begin_checkout', 'view_item']
    
    for event_name in event_names:
        for source in sources[:2]:
            for medium in mediums[:2]:
                for day_offset in range(7):
                    date = base_date + timedelta(days=day_offset)
                    
                    key_events = random.randint(5, 50) if event_name == 'purchase' else random.randint(10, 100)
                    
                    conversion_data.append({
                        'property_id': property_id,
                        'date': date.strftime('%Y-%m-%d'),
                        'event_name': event_name,
                        'session_source': source,
                        'session_medium': medium,
                        'key_events': key_events,
                        'event_count': key_events * random.randint(1, 3),
                        'total_revenue': round(key_events * random.uniform(100, 500), 2) if event_name == 'purchase' else 0,
                        'transactions': key_events if event_name == 'purchase' else 0,
                        'purchase_revenue': round(key_events * random.uniform(100, 500), 2) if event_name == 'purchase' else 0,
                        'collected_at': datetime.now().isoformat()
                    })
    
    for idx, data in enumerate(conversion_data, start=1):
        db.conn.execute("""
            INSERT INTO conversions (id, property_id, date, event_name, session_source, session_medium,
                                   key_events, event_count, total_revenue, transactions,
                                   purchase_revenue, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            idx, data['property_id'], data['date'], data['event_name'], data['session_source'],
            data['session_medium'], data['key_events'], data['event_count'], data['total_revenue'],
            data['transactions'], data['purchase_revenue'], data['collected_at']
        ])
    
    print(f"  ✓ {len(conversion_data)} registros de conversões inseridos")
    
    # 4. Inserir dados de GSC (Search Console) - Query Performance
    print("  → Inserindo dados de Search Console (queries)...")
    gsc_query_data = []
    site_url = "https://www.example.com/"
    queries = [
        "melhor notebook 2025",
        "mouse gamer barato",
        "teclado mecânico para programação",
        "como escolher notebook",
        "review mouse logitech",
        "cadeira gamer confortável"
    ]
    
    for query in queries:
        for day_offset in range(0, 7, 2):  # A cada 2 dias (período de 2 dias)
            start_date = base_date + timedelta(days=day_offset)
            end_date = start_date + timedelta(days=1)
            impressions = random.randint(100, 5000)
            clicks = int(impressions * random.uniform(0.01, 0.15))
            
            gsc_query_data.append({
                'site_url': site_url,
                'query': query,
                'clicks': clicks,
                'impressions': impressions,
                'ctr': round(clicks / impressions, 4) if impressions > 0 else 0,
                'position': round(random.uniform(1, 50), 1),
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'collected_at': datetime.now().isoformat()
            })
    
    for idx, data in enumerate(gsc_query_data, start=1):
        db.conn.execute("""
            INSERT INTO gsc_query_performance (id, site_url, query, clicks, impressions, ctr, 
                                              position, start_date, end_date, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            idx, data['site_url'], data['query'], data['clicks'], data['impressions'],
            data['ctr'], data['position'], data['start_date'], data['end_date'], data['collected_at']
        ])
    
    print(f"  ✓ {len(gsc_query_data)} registros de GSC (queries) inseridos")
    
    # 5. Inserir dados de GSC - Page Performance
    print("  → Inserindo dados de Search Console (páginas)...")
    gsc_page_data = []
    
    for page in pages:
        for day_offset in range(0, 7, 2):
            start_date = base_date + timedelta(days=day_offset)
            end_date = start_date + timedelta(days=1)
            impressions = random.randint(100, 5000)
            clicks = int(impressions * random.uniform(0.01, 0.15))
            
            gsc_page_data.append({
                'site_url': site_url,
                'page': site_url + page.lstrip('/'),
                'clicks': clicks,
                'impressions': impressions,
                'ctr': round(clicks / impressions, 4) if impressions > 0 else 0,
                'position': round(random.uniform(1, 50), 1),
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'collected_at': datetime.now().isoformat()
            })
    
    for idx, data in enumerate(gsc_page_data, start=1):
        db.conn.execute("""
            INSERT INTO gsc_page_performance (id, site_url, page, clicks, impressions, ctr,
                                            position, start_date, end_date, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            idx, data['site_url'], data['page'], data['clicks'], data['impressions'],
            data['ctr'], data['position'], data['start_date'], data['end_date'], data['collected_at']
        ])
    
    print(f"  ✓ {len(gsc_page_data)} registros de GSC (páginas) inseridos")
    
    # Verificar totais
    print("\n📊 Resumo dos dados inseridos:")
    print(f"  • Traffic: {db.conn.execute('SELECT COUNT(*) FROM traffic').fetchone()[0]} registros")
    print(f"  • Engagement: {db.conn.execute('SELECT COUNT(*) FROM engagement').fetchone()[0]} registros")
    print(f"  • Conversions: {db.conn.execute('SELECT COUNT(*) FROM conversions').fetchone()[0]} registros")
    print(f"  • GSC Query Performance: {db.conn.execute('SELECT COUNT(*) FROM gsc_query_performance').fetchone()[0]} registros")
    print(f"  • GSC Page Performance: {db.conn.execute('SELECT COUNT(*) FROM gsc_page_performance').fetchone()[0]} registros")
    
    db.close()
    print("\n✅ Dados de teste criados com sucesso!")
    print("⚠️  LEMBRE-SE: Execute 'python tests/cleanup_test_data.py' para limpar depois!")


if __name__ == "__main__":
    generate_test_data()
