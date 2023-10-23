#include "llvm/Pass.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/DebugInfoMetadata.h"
#include <filesystem>
#include <string>

using namespace llvm;

namespace {

struct itargetsPass : public PassInfoMixin<itargetsPass> {
    PreservedAnalyses run(Module &M, ModuleAnalysisManager &AM) {
        for (auto &F : M) {
			for (auto &BB : F) {
				for (auto &I : BB) {				
					if (CallInst *CI = dyn_cast<CallInst>(&I)) {
						Function *calledFunction = CI->getCalledFunction();
							if (!calledFunction) {
								if (DILocation *Loc = CI->getDebugLoc()) {
								  	unsigned line = Loc->getLine();
								  	StringRef file = Loc->getFilename();
									// maybe some file will be file/n/a/m/e.c ???
								  	outs() << file.substr(file.find_last_of("/\\") + 1) << ":" << line << "\n";
								}
							}
					}				
				}
			}
        }
        return PreservedAnalyses::all();
    };
};

}

extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
    return {
        .APIVersion = LLVM_PLUGIN_API_VERSION,
        .PluginName = "itargets pass",
        .PluginVersion = "v0.1",
        .RegisterPassBuilderCallbacks = [](PassBuilder &PB) {
            PB.registerPipelineStartEPCallback(
                [](ModulePassManager &MPM, OptimizationLevel Level) {
                    MPM.addPass(itargetsPass());
                });
        }
    };
}
