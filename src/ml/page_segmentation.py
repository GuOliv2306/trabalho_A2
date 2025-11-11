import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Any

class PageSegmenter:
    """
    Realiza o clustering de páginas com base em métricas de engajamento.

    Métricas esperadas: engajamento, eventos, duração.
    """
    def __init__(self, n_clusters: int = 5, random_state: int = 42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=self.random_state, n_init='auto')
        self.scaler = StandardScaler()
        self.features = ['engagement_rate', 'event_count', 'average_session_duration']

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica o pré-processamento e o clustering ao DataFrame.

        Args:
            df: DataFrame com as colunas 'page_path' e as métricas de clustering.

        Returns:
            DataFrame original com uma nova coluna 'cluster' contendo o ID do cluster.
        """
        if not all(feature in df.columns for feature in self.features):
            raise ValueError(f"O DataFrame deve conter as colunas: {self.features}")

        # 1. Preparação dos dados
        df_features = df[self.features].copy()

        # 2. Normalização
        scaled_features = self.scaler.fit_transform(df_features)

        # 3. Clustering
        df['cluster'] = self.kmeans.fit_predict(scaled_features)

        return df

    def get_cluster_centers(self) -> pd.DataFrame:
        """
        Retorna os centros dos clusters (média das features normalizadas).
        """
        centers = self.scaler.inverse_transform(self.kmeans.cluster_centers_)
        return pd.DataFrame(centers, columns=self.features).round(2)

    def get_segment_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Gera um resumo dos segmentos (clusters).
        """
        summary = df.groupby('cluster')[self.features].mean().reset_index()
        summary = summary.rename(columns={col: f'avg_{col}' for col in self.features})
        summary['count'] = df.groupby('cluster').size().values
        return summary.round(2)

# Exemplo de uso (simulado)
if __name__ == '__main__':
    # Dados simulados
    data = {
        'page_path': ['/home', '/blog/post1', '/product/a', '/product/b', '/about', '/contact'],
        'engagement_rate': [0.6, 0.8, 0.4, 0.9, 0.5, 0.3],
        'event_count': [100, 500, 50, 1200, 80, 20],
        'average_session_duration': [120, 300, 60, 450, 90, 30]
    }
    df_pages = pd.DataFrame(data)

    # Inicializa e aplica o segmentador
    segmenter = PageSegmenter(n_clusters=3)
    df_clustered = segmenter.fit_transform(df_pages)

    print("--- DataFrame com Clusters ---")
    print(df_clustered)

    print("\n--- Centros dos Clusters (Valores Reais) ---")
    print(segmenter.get_cluster_centers())

    print("\n--- Resumo dos Segmentos ---")
    print(segmenter.get_segment_summary(df_clustered))
