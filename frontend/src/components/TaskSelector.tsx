import { TASK_GROUPS, TaskType, TaskConfig, TaskGroup } from '../types';

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

  // 渲染单个任务卡片
  const renderTaskCard = (task: TaskConfig, group: TaskGroup) => {
    const isSelected = selectedTask === task.id;
    const isYolo = group.id === 'yolo';
    
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
          relative cursor-pointer rounded-xl border-2 p-3 transition-all
          ${isSelected 
            ? isYolo 
              ? 'border-amber-500 bg-amber-50 shadow-md' 
              : 'border-blue-500 bg-blue-50 shadow-md'
            : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
          }
          ${disabled ? 'cursor-not-allowed opacity-50' : ''}
        `}
      >
        {/* 选中标记 */}
        {isSelected && (
          <div className={`absolute right-2 top-2 flex h-5 w-5 items-center justify-center rounded-full ${isYolo ? 'bg-amber-500' : 'bg-blue-500'}`}>
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
        <div className="mb-1 text-xl">{task.icon}</div>

        {/* 标题 */}
        <h4 className={`text-sm font-medium ${isSelected ? (isYolo ? 'text-amber-700' : 'text-blue-700') : 'text-gray-800'}`}>
          {task.name}
        </h4>

        {/* 描述 */}
        <p className="mt-0.5 text-xs text-gray-500 line-clamp-1">
          {task.description}
        </p>
      </div>
    );
  };

  // 渲染任务分组
  const renderTaskGroup = (group: TaskGroup) => {
    return (
      <div key={group.id} className={`rounded-2xl border ${group.borderColor} ${group.bgColor} p-4`}>
        {/* 分组标题 */}
        <div className="mb-3 flex items-center gap-2">
          <span className="text-lg">{group.icon}</span>
          <div>
            <h4 className={`text-sm font-semibold ${group.color}`}>{group.name}</h4>
            <p className="text-xs text-gray-500">{group.description}</p>
          </div>
        </div>

        {/* 任务卡片网格 */}
        <div className="grid grid-cols-2 gap-2">
          {group.tasks.map((task) => renderTaskCard(task, group))}
        </div>
      </div>
    );
  };

  return (
    <div className="w-full">
      <h3 className="mb-3 text-sm font-medium text-gray-700">选择识别任务</h3>
      <div className="space-y-4">
        {TASK_GROUPS.map((group) => renderTaskGroup(group))}
      </div>
    </div>
  );
};

export default TaskSelector;
