import { TASKS, TaskType, TaskConfig } from '../types';

interface TaskSelectorProps {
  selectedTask: TaskType;
  onTaskSelect: (task: TaskType) => void;
  disabled?: boolean;
}

const TaskSelector = ({ selectedTask, onTaskSelect, disabled = false }: TaskSelectorProps) => {
  const handleSelect = (task: TaskConfig) => {
    if (!disabled) {
      onTaskSelect(task.id);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent, task: TaskConfig) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleSelect(task);
    }
  };

  return (
    <div className="w-full">
      <h3 className="mb-3 text-sm font-medium text-gray-700">选择识别任务</h3>
      <div className="grid grid-cols-2 gap-3">
        {TASKS.map((task) => {
          const isSelected = selectedTask === task.id;
          return (
            <div
              key={task.id}
              onClick={() => handleSelect(task)}
              onKeyDown={(e) => handleKeyDown(e, task)}
              role="button"
              tabIndex={disabled ? -1 : 0}
              aria-label={`选择${task.name}任务`}
              aria-pressed={isSelected}
              className={`
                relative cursor-pointer rounded-xl border-2 p-4 transition-all
                ${isSelected 
                  ? 'border-primary-500 bg-primary-50 shadow-md' 
                  : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                }
                ${disabled ? 'cursor-not-allowed opacity-50' : ''}
              `}
            >
              {/* 选中标记 */}
              {isSelected && (
                <div className="absolute right-2 top-2 flex h-5 w-5 items-center justify-center rounded-full bg-primary-500">
                  <svg
                    className="h-3 w-3 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={3}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
              )}

              {/* 图标 */}
              <div className="mb-2 text-2xl">{task.icon}</div>

              {/* 标题 */}
              <h4 className={`font-medium ${isSelected ? 'text-primary-700' : 'text-gray-800'}`}>
                {task.name}
              </h4>

              {/* 描述 */}
              <p className="mt-1 text-xs text-gray-500 line-clamp-2">
                {task.description}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TaskSelector;
