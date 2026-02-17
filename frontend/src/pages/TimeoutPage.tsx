import { Layout } from '../components/Layout';
import { motion } from 'framer-motion';

export function TimeoutPage() {
  return (
    <Layout
      title="Технические работы"
      subtitle="Извините за неудобства, скоро всё починим"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="max-w-md mx-auto mt-10 p-8 bg-dark-card border border-dark-border rounded-lg"
      >
        <div className="text-6xl mb-4 text-center">🔧</div>
        <h2 className="text-2xl font-bold mb-4 text-center">
          Ведутся технические работы
        </h2>
        <p className="text-dark-textLight text-center">
          Мы работаем над улучшением сервиса. Пожалуйста, вернитесь позже.
        </p>
      </motion.div>
    </Layout>
  );
}
