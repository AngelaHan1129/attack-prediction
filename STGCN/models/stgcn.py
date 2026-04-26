# models/stgcn.py
import torch
import torch.nn as nn
import torch.nn.functional as F


class STGCNBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=(9, 1), stride=1, dropout=0.2):
        super().__init__()

        assert kernel_size[0] % 2 == 1, "Temporal kernel size should be odd."
        padding = ((kernel_size[0] - 1) // 2, 0)

        self.gcn = nn.Conv2d(in_channels, out_channels, kernel_size=1)

        self.tcn = nn.Sequential(
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(
                out_channels,
                out_channels,
                kernel_size=kernel_size,
                stride=(stride, 1),
                padding=padding
            ),
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
        # x: (N, C, T, V)
        res = self.residual(x)
        x = self.gcn(x)
        x = self.tcn(x)
        x = x + res
        x = self.relu(x)
        return x


class SimpleSTGCN(nn.Module):
    def __init__(self, in_channels=3, num_class=3, num_point=33, num_person=1):
        super().__init__()

        self.in_channels = in_channels
        self.num_class = num_class
        self.num_point = num_point
        self.num_person = num_person

        self.data_bn = nn.BatchNorm1d(num_person * in_channels * num_point)

        self.layer1 = STGCNBlock(in_channels, 64, kernel_size=(9, 1), stride=1, dropout=0.2)
        self.layer2 = STGCNBlock(64, 64, kernel_size=(9, 1), stride=1, dropout=0.2)
        self.layer3 = STGCNBlock(64, 128, kernel_size=(9, 1), stride=2, dropout=0.2)
        self.layer4 = STGCNBlock(128, 128, kernel_size=(9, 1), stride=1, dropout=0.2)
        self.layer5 = STGCNBlock(128, 256, kernel_size=(9, 1), stride=2, dropout=0.2)
        self.layer6 = STGCNBlock(256, 256, kernel_size=(9, 1), stride=1, dropout=0.2)

        self.fc = nn.Linear(256, num_class)

    def forward(self, x):
        # x shape: (N, C, T, V, M)
        if x.ndim != 5:
            raise ValueError(f"Input must be 5D (N, C, T, V, M), got shape {x.shape}")

        N, C, T, V, M = x.size()

        if C != self.in_channels:
            raise ValueError(f"Expected input channels={self.in_channels}, but got {C}")
        if V != self.num_point:
            raise ValueError(f"Expected num_point={self.num_point}, but got {V}")
        if M != self.num_person:
            raise ValueError(f"Expected num_person={self.num_person}, but got {M}")

        # Normalize input
        # (N, C, T, V, M) -> (N, M, V, C, T)
        x = x.permute(0, 4, 3, 1, 2).contiguous()

        # (N, M, V, C, T) -> (N, M*V*C, T)
        x = x.view(N, M * V * C, T)
        x = self.data_bn(x)

        # (N, M*V*C, T) -> (N, M, V, C, T)
        x = x.view(N, M, V, C, T)

        # (N, M, V, C, T) -> (N, M, C, T, V)
        x = x.permute(0, 1, 3, 4, 2).contiguous()

        # merge person dim
        # (N, M, C, T, V) -> (N*M, C, T, V)
        x = x.view(N * M, C, T, V)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = self.layer5(x)
        x = self.layer6(x)

        # global average pooling on T, V
        x = F.avg_pool2d(x, kernel_size=x.size()[2:])  # (N*M, 256, 1, 1)
        x = x.view(N, M, -1)                           # (N, M, 256)
        x = x.mean(dim=1)                              # average over persons -> (N, 256)

        x = self.fc(x)                                 # (N, num_class)
        return x