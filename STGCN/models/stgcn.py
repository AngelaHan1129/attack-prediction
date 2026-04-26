# models/stgcn.py
import torch
import torch.nn as nn
import torch.nn.functional as F

class STGCNBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=(9, 1), stride=1, dropout=0.2):
        super().__init__()
        padding = ((kernel_size[0] - 1) // 2, 0)

        self.gcn = nn.Conv2d(in_channels, out_channels, kernel_size=1)
        self.tcn = nn.Sequential(
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=kernel_size, stride=(stride, 1), padding=padding),
            nn.BatchNorm2d(out_channels),
            nn.Dropout(dropout)
        )

        if in_channels != out_channels or stride != 1:
            self.residual = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=(stride, 1)),
                nn.BatchNorm2d(out_channels)
            )
        else:
            self.residual = nn.Identity()

        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        res = self.residual(x)
        x = self.gcn(x)
        x = self.tcn(x)
        x = x + res
        return self.relu(x)

class SimpleSTGCN(nn.Module):
    def __init__(self, in_channels=3, num_class=3, num_point=33, num_person=1):
        super().__init__()
        self.data_bn = nn.BatchNorm1d(num_person * in_channels * num_point)

        self.layers = nn.Sequential(
            STGCNBlock(in_channels, 64),
            STGCNBlock(64, 64),
            STGCNBlock(64, 128, stride=2),
            STGCNBlock(128, 128),
            STGCNBlock(128, 256, stride=2),
            STGCNBlock(256, 256)
        )

        self.fc = nn.Linear(256, num_class)

    def forward(self, x):
        # x: (N, C, T, V, M)
        N, C, T, V, M = x.size()

        x = x.permute(0, 4, 3, 1, 2).contiguous()   # N, M, V, C, T
        x = x.view(N, M * V * C, T)
        x = self.data_bn(x)
        x = x.view(N, M, V, C, T)
        x = x.permute(0, 1, 3, 4, 2).contiguous()   # N, M, C, T, V
        x = x.view(N * M, C, T, V)

        x = self.layers(x)
        x = F.avg_pool2d(x, x.size()[2:])           # global pooling
        x = x.view(N, M, -1).mean(dim=1)            # average over persons
        x = self.fc(x)

        return x