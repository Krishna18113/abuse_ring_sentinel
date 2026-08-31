import torch
import torch.nn as nn
from torch_geometric.nn import SAGEConv, HeteroConv

class HeteroGraphSAGE(torch.nn.Module):
    """Heterogeneous GraphSAGE architecture for Customer node classification."""
    
    def __init__(self, metadata, hidden_channels, out_channels=2, dropout=0.3):
        super().__init__()
        
        # Linear projection encoders for each node type to hidden_channels
        self.encoder = nn.ModuleDict({
            "customer": nn.Linear(20, hidden_channels),
            "transaction": nn.Linear(5, hidden_channels),
            "device": nn.Linear(1, hidden_channels),
            "ip": nn.Linear(1, hidden_channels),
            "coupon": nn.Linear(1, hidden_channels)
        })
        
        # Layer 1 message passing: aggregate hidden representations from connected nodes
        self.conv1 = HeteroConv({
            edge_type: SAGEConv((hidden_channels, hidden_channels), hidden_channels)
            for edge_type in metadata[1]
        }, aggr="sum")
        
        # Layer 2 message passing
        self.conv2 = HeteroConv({
            edge_type: SAGEConv((hidden_channels, hidden_channels), hidden_channels)
            for edge_type in metadata[1]
        }, aggr="sum")
        
        # Final classification layers
        self.classifier = nn.Sequential(
            nn.Linear(hidden_channels, hidden_channels),
            nn.ReLU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_channels, out_channels)
        )
        
    def forward(self, x_dict, edge_index_dict):
        # 1. Project input feature dimensions to hidden_channels
        h_dict = {}
        for node_type, x in x_dict.items():
            h_dict[node_type] = self.encoder[node_type](x)
            
        # 2. First Layer of Heterogeneous message passing & Activation
        h_dict = self.conv1(h_dict, edge_index_dict)
        h_dict = {node_type: torch.relu(h) for node_type, h in h_dict.items()}
        
        # 3. Second Layer of message passing & Activation
        h_dict = self.conv2(h_dict, edge_index_dict)
        h_dict = {node_type: torch.relu(h) for node_type, h in h_dict.items()}
        
        # 4. Binary logit classification of customer embeddings
        cust_emb = h_dict["customer"]
        logits = self.classifier(cust_emb)
        return logits, cust_emb
