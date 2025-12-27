import torch
import torch.nn as nn

class EtchDepthModel(nn.Module):
    def __init__(self):
        super(EtchDepthModel, self).__init__()
        # Sensor inputs: 5 (rf, press, gas1, gas2, temp)
        # Image inputs: 4 (r, g, b, edge)
        self.fc1 = nn.Linear(5 + 4, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 1) # Output: Depth (microns)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)

def save_dummy_model(path='model.pth'):
    model = EtchDepthModel()
    torch.save(model.state_dict(), path)

if __name__ == "__main__":
    save_dummy_model()
