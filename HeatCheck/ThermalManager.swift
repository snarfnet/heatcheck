import AVFoundation
import Combine
import SwiftUI

enum ThermalState: Equatable {
    case cool
    case normal
    case warm
    case hot
    case critical
    case recovering
}

enum UserAction {
    case dimScreen
    case removeCase
    case pauseApp
    case unplug
    case lowPower
}

final class ThermalManager: NSObject, ObservableObject {
    @Published var state: ThermalState = .normal
    @Published var currentLine: String = "今の熱状態を見ているよ"
    @Published var stateText: String = "通常"
    @Published var statusDetail: String = "iOSの熱状態は通常です。"
    @Published var shouldShowTips: Bool = false

    private var timer: Timer?
    private var lastSpokenLine: String?
    private let synthesizer = AVSpeechSynthesizer()
    private let lineDatabase = LineDatabase()

    override init() {
        super.init()
    }

    func startMonitoring() {
        guard timer == nil else { return }

        NotificationCenter.default.addObserver(
            self,
            selector: #selector(thermalStateDidChange),
            name: ProcessInfo.thermalStateDidChangeNotification,
            object: nil
        )

        timer = Timer.scheduledTimer(withTimeInterval: 8.0, repeats: true) { [weak self] _ in
            self?.updateState(speak: false)
        }

        updateState(speak: true)
    }

    @objc private func thermalStateDidChange() {
        updateState(speak: true)
    }

    private func updateState(speak: Bool) {
        let thermalState = ProcessInfo.processInfo.thermalState
        state = state(for: thermalState)
        stateText = label(for: state)
        statusDetail = detail(for: thermalState)
        shouldShowTips = state == .warm || state == .hot || state == .critical

        currentLine = lineDatabase.getLine(for: state)
        if speak {
            speakLine(currentLine)
        }
    }

    private func state(for thermalState: ProcessInfo.ThermalState) -> ThermalState {
        switch thermalState {
        case .nominal:
            return .normal
        case .fair:
            return .warm
        case .serious:
            return .hot
        case .critical:
            return .critical
        @unknown default:
            return .normal
        }
    }

    private func label(for state: ThermalState) -> String {
        switch state {
        case .cool:
            return "涼しめ"
        case .normal:
            return "通常"
        case .warm:
            return "少し熱い"
        case .hot:
            return "熱い"
        case .critical:
            return "かなり熱い"
        case .recovering:
            return "対策メモ"
        }
    }

    private func detail(for thermalState: ProcessInfo.ThermalState) -> String {
        switch thermalState {
        case .nominal:
            return "iOSの熱状態は通常です。端末をそのまま使えます。"
        case .fair:
            return "iOSが少し熱を持っている状態として扱っています。"
        case .serious:
            return "iOSが高めの熱状態として扱っています。少し休ませるのがおすすめです。"
        case .critical:
            return "iOSがかなり高い熱状態として扱っています。充電や重い処理を止めてください。"
        @unknown default:
            return "iOSから取得した熱状態の目安です。"
        }
    }

    func userAction(_ action: UserAction) {
        state = .recovering
        stateText = "対策メモ"
        statusDetail = "このボタンは対策のメモです。端末の温度を測定したり、下げたりするものではありません。"
        shouldShowTips = true

        let responseLine = lineDatabase.getResponseLine(for: action)
        currentLine = responseLine
        speakLine(responseLine)

        DispatchQueue.main.asyncAfter(deadline: .now() + 5) { [weak self] in
            self?.updateState(speak: false)
        }
    }

    private func speakLine(_ text: String) {
        guard lastSpokenLine != text else { return }
        lastSpokenLine = text

        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "ja-JP")
        utterance.rate = 0.5
        utterance.pitchMultiplier = 1.15

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

final class LineDatabase {
    private let lines: [ThermalState: [String]] = [
        .cool: [
            "涼しめでいい感じ",
            "今は落ち着いているよ",
            "このまま様子を見よう",
        ],
        .normal: [
            "今は通常だよ",
            "無理なく使えそう",
            "熱状態は落ち着いているよ",
            "様子を見ていこう",
        ],
        .warm: [
            "少し熱を持っているみたい",
            "明るさを少し下げてもいいかも",
            "ケースを外すと楽になることがあるよ",
            "重いアプリは少し休ませよう",
        ],
        .hot: [
            "熱状態が高めだよ",
            "少し休ませてあげよう",
            "充電中なら一度止めるのもあり",
            "動画やゲームは休憩しよう",
        ],
        .critical: [
            "かなり熱い状態だよ",
            "すぐに休ませてね",
            "充電と重い処理を止めよう",
            "涼しい場所で様子を見よう",
        ],
        .recovering: [
            "対策をメモしたよ",
            "無理せず様子を見よう",
            "少し休ませてあげてね",
        ],
    ]

    private let responseLines: [UserAction: [String]] = [
        .dimScreen: [
            "明るさを下げるのはいい対策だよ",
            "画面を少し暗くして様子を見よう",
        ],
        .removeCase: [
            "ケースを外すと熱が逃げやすいよ",
            "風通しをよくしてあげよう",
        ],
        .pauseApp: [
            "重いアプリを休ませよう",
            "ゲームや動画は少し休憩だね",
        ],
        .unplug: [
            "充電を止めて様子を見よう",
            "熱い時の充電は少し休ませてね",
        ],
        .lowPower: [
            "低電力モードも助けになるよ",
            "負荷を下げてゆっくりいこう",
        ],
    ]

    func getLine(for state: ThermalState) -> String {
        lines[state]?.randomElement() ?? "様子を見ているよ"
    }

    func getResponseLine(for action: UserAction) -> String {
        responseLines[action]?.randomElement() ?? "対策をメモしたよ"
    }
}
