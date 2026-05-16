import SwiftUI

struct ContentView: View {
    @StateObject var thermalManager = ThermalManager()

    var body: some View {
        ZStack {
            backgroundGradient(for: thermalManager.currentTemp)
                .ignoresSafeArea()

            VStack(spacing: 20) {
                Text("HeatCheck")
                    .font(.system(size: 28, weight: .bold))
                    .foregroundColor(.white)

                Spacer()

                VStack(spacing: 10) {
                    Text("\(Int(thermalManager.currentTemp))°C")
                        .font(.system(size: 72, weight: .bold))
                        .foregroundColor(.white)

                    Text(thermalManager.stateText)
                        .font(.system(size: 16))
                        .foregroundColor(.white.opacity(0.8))
                }

                Spacer()

                CharacterView(state: thermalManager.state, text: thermalManager.currentLine)

                Spacer()

                VStack(spacing: 12) {
                    HStack(spacing: 12) {
                        ActionButton(icon: "🌬️", label: "扇風機", action: {
                            thermalManager.userAction(.fan)
                        })

                        ActionButton(icon: "🧊", label: "冷たい飲み物", action: {
                            thermalManager.userAction(.drink)
                        })

                        ActionButton(icon: "❄️", label: "冷房", action: {
                            thermalManager.userAction(.ac)
                        })
                    }

                    HStack(spacing: 12) {
                        ActionButton(icon: "🧣", label: "冷たいタオル", action: {
                            thermalManager.userAction(.towel)
                        })

                        ActionButton(icon: "🔋", label: "Low Power", action: {
                            thermalManager.userAction(.lowPower)
                        })
                    }
                }
                .padding(.horizontal)

                Spacer()

                if thermalManager.shouldShowTips {
                    CoolingTipsView()
                }
            }
            .padding()
        }
        .onAppear {
            thermalManager.startMonitoring()
        }
    }

    func backgroundGradient(for temp: Double) -> LinearGradient {
        if temp < 30 {
            return LinearGradient(gradient: Gradient(colors: [Color.blue, Color.cyan]),
                                startPoint: .topLeading, endPoint: .bottomTrailing)
        } else if temp < 35 {
            return LinearGradient(gradient: Gradient(colors: [Color.green, Color.yellow]),
                                startPoint: .topLeading, endPoint: .bottomTrailing)
        } else if temp < 40 {
            return LinearGradient(gradient: Gradient(colors: [Color.yellow, Color.orange]),
                                startPoint: .topLeading, endPoint: .bottomTrailing)
        } else {
            return LinearGradient(gradient: Gradient(colors: [Color.red, Color.orange]),
                                startPoint: .topLeading, endPoint: .bottomTrailing)
        }
    }
}

struct ActionButton: View {
    let icon: String
    let label: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 6) {
                Text(icon)
                    .font(.system(size: 24))
                Text(label)
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(.white)
            }
            .frame(maxWidth: .infinity)
            .padding(12)
            .background(Color.white.opacity(0.2))
            .cornerRadius(12)
        }
    }
}

struct CharacterView: View {
    let state: ThermalState
    let text: String

    private var imageName: String {
        HeatGirlExpression.imageName(for: state, line: text)
    }

    var body: some View {
        VStack(spacing: 8) {
            Image(imageName)
                .resizable()
                .scaledToFit()
                .frame(width: 230, height: 230)
                .scaleEffect(state == .critical ? 1.1 : 1.0)
                .shadow(color: Color.black.opacity(0.18), radius: 14, x: 0, y: 8)
                .accessibilityHidden(true)

            Text("\"\(text)\"")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(.white)
                .padding(12)
                .background(Color.white.opacity(0.2))
                .cornerRadius(8)
                .lineLimit(2)
        }
    }
}

struct HeatGirlExpression {
    static func imageName(for state: ThermalState, line: String) -> String {
        let stateName: String
        switch state {
        case .cool:
            stateName = "cool"
        case .normal:
            stateName = "normal"
        case .warm:
            stateName = "warm"
        case .hot:
            stateName = "hot"
        case .critical:
            stateName = "critical"
        case .recovering:
            stateName = "recovering"
        }

        return "heatgirl_\(stateName)_\(String(format: "%02d", stableExpressionIndex(for: line)))"
    }

    private static func stableExpressionIndex(for line: String) -> Int {
        let seed = line.unicodeScalars.reduce(0) { partial, scalar in
            (partial + Int(scalar.value)) % 9973
        }
        return (seed % 5) + 1
    }
}

struct CoolingTipsView: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("🧊 冷却のコツ")
                .font(.system(size: 14, weight: .bold))
                .foregroundColor(.white)

            VStack(alignment: .leading, spacing: 6) {
                TipRow("画面の明るさを下げる")
                TipRow("ケースを外す")
                TipRow("ゲームを閉じる")
                TipRow("ビデオ撮影を停止")
            }
            .font(.system(size: 12))
            .foregroundColor(.white.opacity(0.9))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(Color.black.opacity(0.3))
        .cornerRadius(8)
    }
}

struct TipRow: View {
    let text: String

    init(_ text: String) {
        self.text = text
    }

    var body: some View {
        HStack(spacing: 6) {
            Text("•")
            Text(text)
        }
    }
}

#Preview {
    ContentView()
}
