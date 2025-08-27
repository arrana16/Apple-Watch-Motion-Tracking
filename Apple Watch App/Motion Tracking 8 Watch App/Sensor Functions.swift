//
//  Sensor Functions.swift
//  Motion Tracking 8 Watch App
//
//  Created by Abdur-Rahman Rana on 2025-01-22.
//

import Foundation
import CoreMotion
import SwiftUI
import HealthKit
import WatchConnectivity

final class Model: NSObject, ObservableObject, WCSessionDelegate {
    var workoutSession: HKWorkoutSession?
    var builder: HKLiveWorkoutBuilder?
    
    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        if let e = error {
            print("\(e)")
        }
    }
}

class SensorFunctions {
    let sensorManager = CMBatchedSensorManager()
    let healthStore = HKHealthStore()
    let session = WCSession.default
    
    var model = Model()
    
    private var accelerometerSamples: [String] = ["Time, x, y, z"]
    private var gyroscopeSamples: [String] = ["Time, roll, pitch, yaw"]
    private var heartRateSamples: [(timestamp: Double, bpm: Double)] = []
    
    private var heartRateQuery: HKObserverQuery?
    
    private var startTime: Date? // Track recording start time
        private var endTime: Date?
    
    func startRecordingData() {
        recordMotionData()
        startHeartRateMonitoring()
        
    }
    
    func endRecording() {
        endTime = Date()
        model.builder?.endCollection(withEnd: Date()) { (success, error) in
                if let error = error {
                    print("Error ending workout collection: \(error.localizedDescription)")
                } else if success {
                    print("Workout collection ended successfully")
                }
            }

            model.workoutSession?.end()
            print("Workout session ended")
        sensorManager.stopAccelerometerUpdates()
        sensorManager.stopDeviceMotionUpdates()
        if let query = heartRateQuery {
                    healthStore.stop(query)
                }
        
    
    }
    
    func startWorkout() {
        let configuration = HKWorkoutConfiguration()
        configuration.activityType = .functionalStrengthTraining
        configuration.locationType = .outdoor
        


        do {
            model.workoutSession = try HKWorkoutSession(healthStore: healthStore, configuration: configuration)
            model.builder = model.workoutSession?.associatedWorkoutBuilder()

            model.builder?.dataSource = HKLiveWorkoutDataSource(
                healthStore: healthStore,
                workoutConfiguration: configuration
            )

            let startDate = Date()
            
            model.workoutSession?.startActivity(with: startDate)
            model.builder?.beginCollection(withStart: startDate) { (success, error) in
                if let error = error {
                    print("Error starting workout collection: \(error.localizedDescription)")
                } else if success {
                    print("Workout collection started successfully")
                }
            }

            print("Workout session started")
        } catch {
            print("Failed to start workout session: \(error.localizedDescription)")
        }
    }

    func stopWorkout() {
        endTime = Date()
        model.builder?.endCollection(withEnd: Date()) { (success, error) in
            if let error = error {
                print("Error ending workout collection: \(error.localizedDescription)")
            } else if success {
                print("Workout collection ended successfully")
            }
        }

        model.workoutSession?.end()
        print("Workout session ended")
    }

    
    func getListLength() -> Int {
        return self.gyroscopeSamples.count
    }
    
    private func recordMotionData() {
        self.startTime = Date()
        print(self.startTime)
        
        guard CMBatchedSensorManager.isAccelerometerSupported && CMBatchedSensorManager.isDeviceMotionSupported else {
            print("Not supported")
            return
        }
        
        let configuration = HKWorkoutConfiguration()
           configuration.activityType = .functionalStrengthTraining
           configuration.locationType = .indoor

           do {
               model.workoutSession = try HKWorkoutSession(healthStore: healthStore, configuration: configuration)
               model.builder = model.workoutSession?.associatedWorkoutBuilder()

               model.builder?.dataSource = HKLiveWorkoutDataSource(
                   healthStore: healthStore,
                   workoutConfiguration: configuration
               )

               let startDate = Date()
               model.workoutSession?.startActivity(with: startDate)
               model.builder?.beginCollection(withStart: startDate) { (success, error) in
                   if let error = error {
                       print("Error starting workout collection: \(error.localizedDescription)")
                   } else if success {
                       Task {
                           do {
                               print("6")
                               for try await data in self.sensorManager.accelerometerUpdates() {
                                   for value in data {
                                       let time = value.timestamp
                                       let x = value.acceleration.x
                                       let y = value.acceleration.y
                                       let z = value.acceleration.z
//                                       print("\(time), \(x), \(y), \(z)")
                                       self.accelerometerSamples.append("\(time), \(x), \(y), \(z)")
       //                                print(self.accelerometerSamples.count)
                                   }
                               }
                           } catch {
                               print("Error receiving accelerometer updates: \(error)")
                           }
                       }
       
                   Task {
                       do {
                           for try await data in self.sensorManager.deviceMotionUpdates() {
                               for value in data {
                                   let time = value.timestamp
                                   let angles = value.attitude
                                   let roll = angles.roll
                                   let pitch = angles.pitch
                                   let yaw = angles.yaw
//                                   print("\(time), \(roll), \(pitch), \(yaw)")
                                   self.gyroscopeSamples.append("\(time), \(roll), \(pitch), \(yaw)")
                               }
       
                           }
                       } catch let error as NSError {
                           print("Gyro Error: \(error)")
                       }
                   }
                       
                       
                   }
               }

               print("Workout session started")
           } catch {
               print("Failed to start workout session: \(error.localizedDescription)")
           }
        
                
//
    }
    private func startHeartRateMonitoring() {
        guard let heartRateType = HKObjectType.quantityType(forIdentifier: .heartRate) else {
            print("Heart rate type is not available.")
            return
        }

        // Create a query for live updates
        let heartRateQuery = HKAnchoredObjectQuery(
            type: heartRateType,
            predicate: nil,
            anchor: nil,
            limit: HKObjectQueryNoLimit
        ) { [weak self] query, samples, _, _, error in
            if let error = error {
                print("Error fetching initial heart rate data: \(error.localizedDescription)")
                return
            }

            // Process initial heart rate samples
            if let samples = samples as? [HKQuantitySample] {
                self?.processHeartRateSamples(samples)
            }
        }

        // Add the live update handler
        heartRateQuery.updateHandler = { [weak self] query, samples, _, _, error in
            if let error = error {
                print("Error receiving live heart rate updates: \(error.localizedDescription)")
                return
            }

            // Process live heart rate samples
            if let samples = samples as? [HKQuantitySample] {
                self?.processHeartRateSamples(samples)
            }
        }

        // Execute the query
        healthStore.execute(heartRateQuery)
//        self.heartRateQuery = heartRateQuery
    }



        
    private func processHeartRateSamples(_ samples: [HKQuantitySample]) {
            for sample in samples {
                let bpm = sample.quantity.doubleValue(for: HKUnit.count().unitDivided(by: .minute()))
                let timestamp = sample.startDate.timeIntervalSince1970
                
                print("Live Heart Rate: \(bpm) BPM at timestamp \(timestamp)")
                
                // Store the heart rate sample
                heartRateSamples.append((timestamp, bpm))
            }
        }

    
    func exportMotionDataCSV() -> URL? {
            let motionData = (accelerometerSamples + gyroscopeSamples).joined(separator: "\n")
            return saveCSV(data: motionData, fileName: "MotionData.csv")
        }

    func exportHeartRateDataCSV() -> URL? {
        guard let startTime = self.startTime else {
                print("Recording times not set.")
                return nil
            }
            
            // Filter samples within the recording period
            let filteredHeartRateData = heartRateSamples
                .filter { $0.timestamp >= startTime.timeIntervalSince1970 }
                .map { "\($0.timestamp), \($0.bpm)" }
            
            let heartRateDataString = filteredHeartRateData.joined(separator: "\n")
            return saveCSV(data: heartRateDataString, fileName: "FilteredHeartRateData.csv")
        }

    private func saveCSV(data: String, fileName: String) -> URL? {
        let fileManager = FileManager.default
        do {
            // Use the temporary directory for exporting files
            let tempDir = fileManager.temporaryDirectory
            let fileURL = tempDir.appendingPathComponent(fileName)
            
            // Write data to the file
            try data.write(to: fileURL, atomically: true, encoding: .utf8)
            return fileURL
        } catch {
            print("Failed to save CSV file: \(error.localizedDescription)")
            return nil
        }
    }
}

