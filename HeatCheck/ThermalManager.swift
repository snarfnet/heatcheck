import SwiftUI
import Combine
import AVFoundation

enum ThermalState: Equatable {
    case cool
    case normal
    case warm
    case hot
    case critical
    case recovering
}

enum UserAction {
    case fan
    case drink
    case ac
    case towel
    case lowPower
}

class ThermalManager: NSObject, ObservableObject {
    @Published var currentTemp: Double = 30.0
    @Published var state: ThermalState = .normal
    @Published var currentLine: String = "こんにちは"
    @Published var stateText: String = "通常"
    @Published var shouldShowTips: Bool = false

    private var timer: Timer?
    private var lastHighTempTime: Date?
    private var recoveringUntil: Date?
    private var synthesizer = AVSpeechSynthesizer()

    private let lineDatabase = LineDatabase()

    override init() {
        super.init()
    }

    func startMonitoring() {
        let notificationCenter = NotificationCenter.default
        notificationCenter.addObserver(
            self,
            selector: #selector(thermalStateDidChange),
            name: ProcessInfo.thermalStateDidChangeNotification,
            object: nil
        )

        timer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { [weak self] _ in
            self?.updateTemperature()
        }

        updateState()
    }

    @objc private func thermalStateDidChange() {
        updateState()
    }

    private func updateTemperature() {
        let thermalState = ProcessInfo.processInfo.thermalState

        switch thermalState {
        case .critical:
            currentTemp = Double.random(in: 46...50)
        case .serious:
            currentTemp = Double.random(in: 42...46)
        case .nominal:
            currentTemp = Double.random(in: 25...35)
        case .uncritical:
            currentTemp = Double.random(in: 15...25)
        @unknown default:
            currentTemp = 30.0
        }

        updateState()
    }

    private func updateState() {
        let thermalState = ProcessInfo.processInfo.thermalState

        if let recoveringUntil, Date() < recoveringUntil, thermalState != .critical {
            state = .recovering
            stateText = "回復中"
            shouldShowTips = false
            updateDialogue()
            return
        }

        state = state(for: currentTemp, thermalState: thermalState)
        stateText = label(for: state)
        shouldShowTips = state == .hot || state == .critical

        if state == .hot || state == .critical {
            lastHighTempTime = Date()
        }

        updateDialogue()
    }

    private func state(for temperature: Double, thermalState: ProcessInfo.ThermalState) -> ThermalState {
        switch thermalState {
        case .critical:
            return .critical
        case .serious:
            return temperature >= 45 ? .critical : .hot
        case .nominal, .uncritical:
            if temperature < 28 {
                return .cool
            } else if temperature < 33 {
                return .normal
            } else if temperature < 38 {
                return .warm
            } else if temperature < 45 {
                return .hot
            } else {
                return .critical
            }
        @unknown default:
            return .normal
        }
    }

    private func label(for state: ThermalState) -> String {
        switch state {
        case .cool:
            return "涼しい"
        case .normal:
            return "通常"
        case .warm:
            return "少し熱い"
        case .hot:
            return "暑い"
        case .critical:
            return "危険"
        case .recovering:
            return "回復中"
        }
    }

    private func updateDialogue() {
        let duration = lastHighTempTime != nil ? -lastHighTempTime!.timeIntervalSinceNow : 0
        currentLine = lineDatabase.getLine(for: state, duration: duration)
        speakLine(currentLine)
    }

    func userAction(_ action: UserAction) {
        let responseLine = lineDatabase.getResponseLine(for: action)
        currentLine = responseLine
        speakLine(responseLine)

        withAnimation(.easeInOut(duration: 1.0)) {
            currentTemp -= Double.random(in: 2...5)
            currentTemp = max(15, currentTemp)
            recoveringUntil = Date().addingTimeInterval(8)
            state = .recovering
            stateText = "回復中"
            shouldShowTips = false
        }
    }

    private func speakLine(_ text: String) {
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "ja-JP")
        utterance.rate = 0.5
        utterance.pitchMultiplier = 1.2

        if synthesizer.isSpeaking {
            synthesizer.stopSpeaking(at: .immediate)
        }
        synthesizer.speak(utterance)
    }

    deinit {
        timer?.invalidate()
        NotificationCenter.default.removeObserver(self)
    }
}

class LineDatabase {
    private let lines: [ThermalState: [String]] = [
        .cool: [
            "涼しいね～",
            "快適です",
            "いい気分～",
            "シャキッとしてる",
        ],
        .normal: [
            "いい天気",
            "ちょうどいい",
            "快適ですね",
            "普通に過ごせる",
        ],
        .warm: [
            "あ、ちょっと暖かい",
            "汗をかき始めた",
            "飲み物、欲しい",
            "扇風機、欲しい",
        ],
        .hot: [
            "暑い！",
            "暑いよ～！",
            "マジで暑い",
            "うわ、熱い",
            "これ、やばくない？",
            "あちい～",
            "息、苦しい",
            "汗、ダラダラ",
        ],
        .critical: [
            "ヤバいヤバいヤバい",
            "死ぬ、死ぬ",
            "えっ、何これ",
            "地獄",
            "終わり",
            "（呼吸が荒い）",
        ],
        .recovering: [
            "あ、涼しい",
            "生き返った",
            "ありがとう",
            "気持ちいい～",
        ],
    ]

    private let responseLines: [UserAction: [String]] = [
        .fan: ["あ、風…", "ありがとう", "助かる～", "気持ちいい", "生き返った"],
        .drink: ["あ、冷たい…", "ありがとう", "これ最高", "ごくごく", "ぷはぁ"],
        .ac: ["涼しい…", "ありがとう", "助かった", "気持ちいい～", "えへへ"],
        .towel: ["あ、気持ちいい", "ありがとう", "生き返った", "やさしい…"],
        .lowPower: ["あ、楽になった", "ありがとう", "これで大丈夫"],
    ]

    func getLine(for state: ThermalState, duration: TimeInterval) -> String {
        guard var stateLines = lines[state] else { return "..." }

        if duration > 120 {
            return "…ZZZ"
        } else if duration > 90 {
            return stateLines.last ?? "…"
        } else if duration > 60 {
            return stateLines.count > 1 ? stateLines[stateLines.count - 2] : stateLines[0]
        }

        return stateLines.randomElement() ?? "..."
    }

    func getResponseLine(for action: UserAction) -> String {
        return responseLines[action]?.randomElement() ?? "ありがとう"
    }
}
