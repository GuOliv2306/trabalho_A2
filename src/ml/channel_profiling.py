import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Any

class ChannelProfiler:
    """
    Realiza o clustering de perfis de canal (source/medium) com base em métricas de performance.

    Métricas esperadas: sessions, activeUsers, newUsers, screenPageViews, averageSessionDuration.
    """
    def __init__(self, n_clusters: int = 3, random_state: int = 42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=self.random_state, n_init='auto')
        self.scaler = StandardScaler()
        self.features = ['sessions', 'activeUsers', 'newUsers', 'screenPageViews', 'averageSessionDuration']

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica o pré-processamento e o clustering ao DataFrame.

        Args:
            df: DataFrame com as colunas 'source' e 'medium' e as métricas de clustering.

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
        'source': ['google', 'google', 'facebook', 'email', 'bing', 'direct'],
        'medium': ['organic', 'cpc', 'social', 'newsletter', 'organic', '(none)'],
        'sessions': [1000, 500, 200, 50, 100, 300],
        'activeUsers': [800, 450, 180, 40, 90, 250],
        'newUsers': [500, 100, 50, 10, 30, 50],
        'screenPageViews': [5000, 1500, 600, 100, 300, 900],
        'averageSessionDuration': [180, 120, 90, 60, 150, 210]
    }
    df_channels = pd.DataFrame(data)

    # Inicializa e aplica o perfilador
    profiler = ChannelProfiler(n_clusters=3)
    df_clustered = profiler.fit_transform(df_channels)

    print("--- DataFrame com Clusters ---")
    print(df_clustered)

    print("\n--- Centros dos Clusters (Valores Reais) ---")
    print(profiler.get_cluster_centers())

    print("\n--- Resumo dos Segmentos ---")
    print(profiler.get_segment_summary(df_clustered))
