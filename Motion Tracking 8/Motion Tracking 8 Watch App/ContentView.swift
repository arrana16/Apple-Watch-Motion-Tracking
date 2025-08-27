//
//  ContentView.swift
//  Motion Tracking 8 Watch App
//
//  Created by Abdur-Rahman Rana on 2025-01-22.
//

import CoreMotion
import SwiftUI
import HealthKit
import WatchConnectivity

private enum RecordingState {
    case idle
    case active
}




struct ContentView: View {
    @State private var state: RecordingState = .idle
    @State private var recorded: Bool = false
    @State private var motionDataURL: URL?
    @State private var heartRateDataURL: URL?
        
        let sensorManager = CMBatchedSensorManager()
        let healthStore = HKHealthStore()
        let session = WCSession.default
    var accelerometerSamples: [String] = []
        var gyroscopeSamples: [String] = []
        var heartRateSamples: [String] = []
    
        @StateObject var model = Model()
    
        
    
    let sensorFunctions = SensorFunctions()
    
    
    var body: some View {
            let recordingButtonTitle = state == .idle ? "Start Recording" : "Stop Recording"
        ScrollView {
            VStack {
                Button(action: {
                    if (state == .idle) {
                        sensorFunctions.startRecordingData()
                        state = .active
                        motionDataURL = nil;
                        heartRateDataURL = nil;
                        recorded = true
                    } else {
                        sensorFunctions.endRecording()
                        motionDataURL = sensorFunctions.exportMotionDataCSV()
                        print(motionDataURL)
                        heartRateDataURL = sensorFunctions.exportHeartRateDataCSV()
                        print(heartRateDataURL)
                        print(sensorFunctions.getListLength())
                        state = .idle
                    }
                }) {
                    Text(recordingButtonTitle)
                        .foregroundColor(state == .idle ? .green : .red)
                }
                
                
                Spacer().frame(height: 20)

                    
                HStack {
                    if let motionDataURL = motionDataURL {
                        ShareLink(
                            item: motionDataURL,
                            preview: SharePreview("Motion Data", image: Image(systemName: "waveform.path.ecg"))
                        ) {
                            Text("Motion Data")
                        }
                    }
                    if let heartRateDataURL = heartRateDataURL {
                        ShareLink(
                            item: heartRateDataURL,
                            preview: SharePreview("Heart Rate Data", image: Image(systemName: "heart.fill"))
                        ) {
                            Text("Heart Data")
                        }
                    }
                }
                    
                    
                }
            .navigationTitle("Tennis Motion Data")
            .onAppear {
                self.requestAuthorization()
            }
        }
        }
    
        
        private func requestAuthorization() {
            let typesToShare: Set = [
                HKQuantityType.workoutType()
            ]

            let typesToRead: Set = [
                HKQuantityType.quantityType(forIdentifier: .heartRate)!,
                HKQuantityType.quantityType(forIdentifier: .activeEnergyBurned)!,
                HKQuantityType.quantityType(forIdentifier: .distanceWalkingRunning)!,
                HKQuantityType.quantityType(forIdentifier: .distanceCycling)!,
                HKObjectType.activitySummaryType()
            ]

            healthStore.requestAuthorization(toShare: typesToShare, read: typesToRead) { (success, error) in }
        }
}

#Preview {
    ContentView()
}
