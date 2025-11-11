import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Any

class KeywordClusterer:
    """
    Realiza o clustering de palavras-chave (queries) com base em métricas de performance do GSC.

    Métricas esperadas: clicks, impressions, ctr, position.
    """
    def __init__(self, n_clusters: int = 4, random_state: int = 42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=self.random_state, n_init='auto')
        self.scaler = StandardScaler()
        # 'position' é uma métrica inversa (menor é melhor), mas o StandardScaler
        # lida com a escala. O K-Means agrupará por similaridade.
        self.features = ['clicks', 'impressions', 'ctr', 'position']

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica o pré-processamento e o clustering ao DataFrame.

        Args:
            df: DataFrame com as colunas 'query' e as métricas de clustering.

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
        # Arredondando 'ctr' para 4 casas decimais (percentual) e o resto para 2
        centers_df = pd.DataFrame(centers, columns=self.features)
        centers_df['ctr'] = centers_df['ctr'].round(4)
        centers_df[['clicks', 'impressions', 'position']] = centers_df[['clicks', 'impressions', 'position']].round(2)
        return centers_df

    def get_segment_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Gera um resumo dos segmentos (clusters).
        """
        summary = df.groupby('cluster')[self.features].mean().reset_index()
        summary = summary.rename(columns={col: f'avg_{col}' for col in self.features})
        summary['count'] = df.groupby('cluster').size().values
        summary['avg_ctr'] = summary['avg_ctr'].round(4)
        summary[['avg_clicks', 'avg_impressions', 'avg_position']] = summary[['avg_clicks', 'avg_impressions', 'avg_position']].round(2)
        return summary

# Exemplo de uso (simulado)
if __name__ == '__main__':
    # Dados simulados (16 queries)
    data = {
        'query': [f'query_{i}' for i in range(16)],
        'clicks': [100, 50, 10, 5, 150, 80, 20, 15, 200, 100, 30, 25, 50, 40, 12, 8],
        'impressions': [10000, 5000, 1000, 500, 15000, 8000, 2000, 1500, 20000, 10000, 3000, 2500, 5000, 4000, 1200, 800],
        'ctr': [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01], # Simplificado para o exemplo
        'position': [1.5, 2.1, 5.0, 8.5, 1.1, 3.2, 6.1, 9.0, 1.0, 2.5, 5.5, 8.0, 3.0, 4.5, 7.0, 10.0]
    }
    # Ajustando CTR para ser mais realista e variado
    data['ctr'] = [c/i for c, i in zip(data['clicks'], data['impressions'])]

    df_queries = pd.DataFrame(data)

    # Inicializa e aplica o clusterizador
    clusterer = KeywordClusterer(n_clusters=4)
    df_clustered = clusterer.fit_transform(df_queries)

    print("--- DataFrame com Clusters ---")
    print(df_clustered)

    print("\n--- Centros dos Clusters (Valores Reais) ---")
    print(clusterer.get_cluster_centers())

    print("\n--- Resumo dos Segmentos ---")
    print(clusterer.get_segment_summary(df_clustered))
