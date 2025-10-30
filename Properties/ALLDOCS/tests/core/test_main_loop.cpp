#include <gtest/gtest.h>
#include "core/engine/main_loop.h"
#include "core/engine/determinism.h"

using namespace polylog::engine;
using namespace polylog::core;

class MainLoopTest : public ::testing::Test {
public:
    FrameTimingConfig GetDefaultConfig() {
        FrameTimingConfig cfg;
        cfg.fixed_dt_s = 1.0f / 60.0f;  // 16.67ms
        cfg.max_dt_s = 0.05f;           // 50ms
        cfg.max_accumulator_s = 0.1f;   // 100ms
        cfg.enable_fixed_step = true;
        return cfg;
    }
};

// STAB-005: Fixed-step accumulation
TEST_F(MainLoopTest, AccumulatorAccumulatesCorrectly) {
    MainLoop loop(GetDefaultConfig());
    
    // Feed 30fps input (double dt per frame)
    float dt_30fps = 1.0f / 30.0f;
    
    loop.Update(dt_30fps);
    EXPECT_EQ(loop.GetSimStepsThisFrame(), 1);
    EXPECT_NEAR(loop.GetInterpolationAlpha(), 0.5f, 0.01f);
    
    loop.Update(dt_30fps);
    EXPECT_EQ(loop.GetSimStepsThisFrame(), 1);
    EXPECT_NEAR(loop.GetInterpolationAlpha(), 1.0f, 0.01f);
    
    // Third frame should trigger 2 steps
    loop.Update(dt_30fps);
    EXPECT_EQ(loop.GetSimStepsThisFrame(), 2);
}

TEST_F(MainLoopTest, DeltaTimeClamped) {
    MainLoop loop(GetDefaultConfig());
    
    // Huge spike (100ms, but max is 50ms)
    loop.Update(0.1f);
    
    // Should have clamped to ~3 steps at 16.67ms
    EXPECT_LE(loop.GetSimStepsThisFrame(), 4);
}

TEST_F(MainLoopTest, AccumulatorCaughtUp) {
    MainLoop loop(GetDefaultConfig());
    
    // Simulate a massive frame stall
    loop.Update(0.2f);  // 200ms spike
    
    // Accumulator should be reset/clamped, not infinite steps
    EXPECT_LT(loop.GetAccumulator(), 0.11f);
}

TEST_F(MainLoopTest, InterpolationAlpha) {
    MainLoop loop(GetDefaultConfig());
    
    float dt = 1.0f / 120.0f;  // 120fps input
    loop.Update(dt);
    
    float alpha = loop.GetInterpolationAlpha();
    EXPECT_GT(alpha, 0.0f);
    EXPECT_LT(alpha, 1.0f);
}

TEST_F(MainLoopTest, LegacyVariableDtMode) {
    FrameTimingConfig cfg = GetDefaultConfig();
    cfg.enable_fixed_step = false;
    MainLoop loop(cfg);
    
    loop.Update(0.02f);
    EXPECT_EQ(loop.GetSimStepsThisFrame(), 1);
    EXPECT_FLOAT_EQ(loop.GetInterpolationAlpha(), 1.0f);
    EXPECT_FLOAT_EQ(loop.GetSimTime(), 0.02f);
}

TEST_F(MainLoopTest, SimTimeAccumulates) {
    MainLoop loop(GetDefaultConfig());
    float dt_60fps = 1.0f / 60.0f;
    
    for (int i = 0; i < 60; ++i) {
        loop.Update(dt_60fps);
    }
    
    // After 60 frames at 60fps, should be ~1 second
    EXPECT_NEAR(loop.GetSimTime(), 1.0f, 0.01f);
}

// STAB-006: Determinism mode
class DeterminismTest : public ::testing::Test {};

TEST_F(DeterminismTest, ModeToggle) {
    EXPECT_FALSE(DeterminismMode::IsEnabled());
    
    DeterminismMode::SetEnabled(true);
    EXPECT_TRUE(DeterminismMode::IsEnabled());
    
    DeterminismMode::SetEnabled(false);
    EXPECT_FALSE(DeterminismMode::IsEnabled());
}

TEST_F(DeterminismTest, RNGSeeding) {
    DeterministicRNG rng1(12345);
    DeterministicRNG rng2(12345);
    
    // Same seed should produce identical sequence
    for (int i = 0; i < 100; ++i) {
        EXPECT_EQ(rng1.Next(), rng2.Next());
    }
}

TEST_F(DeterminismTest, RNGDifferentSeeds) {
    DeterministicRNG rng1(12345);
    DeterministicRNG rng2(54321);
    
    // Different seeds should diverge (probabilistically)
    bool diverged = false;
    for (int i = 0; i < 10; ++i) {
        if (rng1.Next() != rng2.Next()) {
            diverged = true;
            break;
        }
    }
    EXPECT_TRUE(diverged);
}

TEST_F(DeterminismTest, FloatRange) {
    DeterministicRNG rng(42);
    
    for (int i = 0; i < 1000; ++i) {
        float f = rng.NextFloat01();
        EXPECT_GE(f, 0.0f);
        EXPECT_LT(f, 1.0f);
    }
}

TEST_F(DeterminismTest, FloatRange2) {
    DeterministicRNG rng(42);
    
    for (int i = 0; i < 1000; ++i) {
        float f = rng.NextFloat(-5.0f, 5.0f);
        EXPECT_GE(f, -5.0f);
        EXPECT_LT(f, 5.0f);
    }
}
