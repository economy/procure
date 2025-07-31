import React from 'react';

// The full sequence of states in the procurement workflow.
const PROCESS_STEPS = [
  'CLARIFYING',
  'EXTRACTING',
  'PROCESSING',
  'FORMATTING',
  'COMPLETED',
];

// A mapping from the backend state names to more user-friendly labels.
const STATE_LABELS: { [key: string]: string } = {
  CLARIFYING: 'Clarifying Query',
  EXTRACTING: 'Extracting Data',
  PROCESSING: 'Processing Results',
  FORMATTING: 'Formatting Output',
  COMPLETED: 'Completed',
  AWAITING_CLARIFICATION: 'Awaiting Your Input',
  ERROR: 'Task Failed',
};

interface StatusStepperProps {
  currentState: string;
}

const StatusStepper: React.FC<StatusStepperProps> = ({ currentState }) => {
  const isAwaitingClarification = currentState === 'AWAITING_CLARIFICATION';
  const isError = currentState === 'ERROR';

  // Find the index of the current step in the workflow.
  const currentStepIndex = PROCESS_STEPS.indexOf(currentState);

  // If the task has failed, display a single error state.
  if (isError) {
    return (
      <div className="flex items-center space-x-2">
        <div className="flex items-center justify-center w-6 h-6 bg-red-500 rounded-full text-white font-bold">
          !
        </div>
        <span className="text-red-500 font-semibold">{STATE_LABELS.ERROR}</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-4 w-full">
      {PROCESS_STEPS.map((step, index) => {
        const isStepCompleted = currentState === 'COMPLETED' || currentStepIndex > index;
        const isCurrentStep = currentStepIndex === index && currentState !== 'COMPLETED';

        // Determine the visual style based on the step's status.
        const circleClass = isStepCompleted
          ? 'bg-green-500'
          : isCurrentStep
          ? 'bg-blue-500 animate-pulse'
          : 'bg-gray-300';
        
        const textClass = isStepCompleted || isCurrentStep ? 'text-gray-800' : 'text-gray-400';

        return (
          <React.Fragment key={step}>
            <div className="flex items-center">
              <div className={`w-4 h-4 rounded-full ${circleClass}`}></div>
              <span className={`ml-2 text-sm font-medium ${textClass}`}>{STATE_LABELS[step]}</span>
            </div>
            {index < PROCESS_STEPS.length - 1 && (
              <div className="flex-1 h-0.5 bg-gray-200"></div>
            )}
          </React.Fragment>
        );
      })}
       {/* Special visual indicator for the paused clarification state */}
      {isAwaitingClarification && (
         <div className="flex items-center text-yellow-500">
            <div className="w-4 h-4 rounded-full bg-yellow-400 animate-pulse mr-2"></div>
            <span className="text-sm font-medium">{STATE_LABELS.AWAITING_CLARIFICATION}</span>
         </div>
       )}
    </div>
  );
};

export default StatusStepper;
